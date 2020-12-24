import subprocess
import logging
import copy
import os

from django.db.models import F
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


from django_q.tasks import async_task
from kinksorter_app.models import PornDirectory, Movie, CurrentTask
from kinksorter_app.apis.api_router import get_correct_api, APIS
from kinksorter_app.functionality.movie_handling import recognize_movie, recognize_multiple


class PornDirectoryHandler:
    scanner = None
    directory = None

    def __init__(self, porn_directory, name='', init_path=None, id_=-1):
        if porn_directory is None and init_path is not None:
            if not os.path.exists(init_path):
                return

            if PornDirectory.objects.filter(path=os.path.abspath(init_path)).exists() \
               or name and PornDirectory.objects.filter(name=name).exists():
                return

            # new_id = max(get_porn_directory_ids()) + 1 if id_ == -1 else id_
            new_id = None if id_ == -1 else id_
            new_porn_dir = PornDirectory(path=os.path.abspath(init_path), name=name, pk=new_id)
            new_porn_dir.save()

            new_porn_dir.create_link_for_video()

            self.directory = new_porn_dir
        else:
            self.directory = get_porn_directory(porn_directory)

        if self.directory is not None:
            self.scanner = MovieScanner(self.directory, APIS)

    def reset(self):
        for movie in self.directory.movies.all():
            movie.delete()
        self.directory.save()

        return self.scan()

    def rerecognize(self):
        target_directory = PornDirectory.objects.get(id=0)
        unrecognized_movies = []
        for movie in self.directory.movies.all():
            movie.scene_id = 0
            movie.save()

            if target_directory:
                target_directory.movies.remove(movie)

            unrecognized_movies.append(movie)

        recognize_multiple(None, unrecognized_movies, wait_for_finish=False)

        return [m.serialize() for m in unrecognized_movies]

    def change_name(self, new_name):
        self.directory.name = new_name
        self.directory.save()
        return True

    def scan(self):
        if self.directory is not None:
            return self.scanner.scan()

    def delete(self):
        if self.directory is not None:
            for movie in self.directory.movies.all():
                movie.delete()

            self.directory.delete()

    def __bool__(self):
        return self.directory is not None


class MovieScanner:
    def __init__(self, porn_directory, apis):
        self.apis = apis    # save in this instance to be able to pickle to the cluster
        self.porn_directory = porn_directory
        self.directory_tree = DirectoryTree(porn_directory.path)
        self._num_trees = 0

    def scan(self):
        self._get_listing(self.directory_tree, recursion_depth=5)
        if settings.USE_ASYNC:
            with transaction.atomic():
                task, _ = CurrentTask.objects.get_or_create(name='Scanning')
                task.progress_max += self._num_trees
                task.save()

        if settings.USE_ASYNC:
            return async_task(self._scan_tree, self.directory_tree)
        else:
            self._scan_tree(self.directory_tree)

    def _get_listing(self, tree, recursion_depth=0):
        recursion_depth -= 1
        for entry in os.scandir(tree.path):
            try:
                if os.path.basename(entry.path).startswith('.'):
                    # skip hidden files (and avoid scanning .git and .kinksorter)
                    # it's your porn folder. there shouldn't be any more hidden files IN that ;)
                    continue
                if entry.is_dir() and recursion_depth > 0:
                    api = tree.api if tree.api else get_correct_api(entry.name, self.apis)
                    new_tree = DirectoryTree(entry.path, prev=tree, api=api)
                    tree.nodes.append(new_tree)
                    name_ = api.name if api else '<None>'
                    logging.info('Scanning directory (API: {}) {}...'.format(name_, entry.path))
                    self._get_listing(new_tree, recursion_depth)

                if entry.is_file() or entry.is_symlink():
                    tree.leafs.append(Leaf(entry.path, self.directory_tree.path))
                    self._num_trees += 1
            except OSError:
                pass

    def _scan_tree(self, tree):
        logging.basicConfig(format='%(message)s',
                            level=logging.DEBUG)
        for leaf in tree.leafs:
            logging.debug('Scanning file {}...'.format(leaf.full_path[-100:]))

            if leaf.is_writeable() and leaf.is_video_file():
                logging.debug('  Adding movie {}...'.format(leaf.full_path[-100:]))
                try:
                    self.add_movie(leaf, tree)
                except ObjectDoesNotExist:
                    # Directory does not exist anymore. Was deleted, so abort Task
                    if settings.USE_ASYNC:
                        current_task = CurrentTask.objects.get(name='Scanning')
                        current_task.progress_current = current_task.progress_max
                        current_task.save()
                    return
            if settings.USE_ASYNC:
                CurrentTask.objects.filter(name='Scanning').update(progress_current=F('progress_current')+1)

        for next_tree in tree.nodes:
            self._scan_tree(next_tree)

    def add_movie(self, leaf, tree):
        api = tree.api if tree.api else self.apis.get('default', None)
        if api is None:
            logging.debug('    No API.')
            return

        if not PornDirectory.objects.filter(id=self.porn_directory.id).exists():
            # Remove race condition movies
            for movie in self.porn_directory.movies.all():
                movie.delete()
            raise ObjectDoesNotExist

        if self.porn_directory.movies.filter(full_path=leaf.full_path).exists():
            logging.debug('    Duplicate movie.')
            return

        if leaf.get_is_link():
            link_path = os.path.realpath(leaf.full_path)
            if Movie.objects.filter(full_path=link_path).exists():
                logging.debug('    Linked Movie is from other porn directory')
                return

        movie = Movie(api=api.name, **leaf.get_file_properties(), from_directory=self.porn_directory.id)
        movie.save()

        recognize_movie(movie, None, api=api)

        if self.porn_directory.movies.filter(full_path=leaf.full_path).exists():
            logging.debug('    Duplicate movie.')
            return

        self.porn_directory.movies.add(movie)
        logging.info('ADDED MOVIE {}...'.format(movie.scene_id))

    def __deepcopy__(self, memodict=None):
        return self


class DirectoryTree:
    # TODO: Maybe rename node/leaf to directory/movie?

    def __init__(self, path, prev=None, api=None, leafs=None, nodes=None):
        self.leafs = []
        if leafs is not None:
            self.leafs = leafs
        self.nodes = []
        if nodes is not None:
            self.nodes = nodes

        self.prev = prev
        self.path = path
        self.api = api

    def __deepcopy__(self, memodict=None):
        return self


class Leaf:
    def __init__(self, full_path, directory_path):
        self.full_path = full_path
        self.directory_path = directory_path

    def is_writeable(self):
        return os.access(self.full_path, os.W_OK)

    def is_video_file(self):
        mime_type = subprocess.check_output(['file', '-b', '--mime-type', self.full_path])
        if mime_type:
            mime_type = mime_type.decode('utf-8')
            if mime_type.startswith('video/') or mime_type.startswith('application/vnd.rn-realmedia'):
                return True
        return False

    def get_file_name(self):
        return os.path.basename(self.full_path)

    def get_file_size(self):
        return os.stat(self.full_path).st_size

    def get_extension(self):
        return os.path.splitext(self.full_path)[-1]

    def get_is_link(self):
        return os.path.islink(self.full_path)

    def get_relative_path(self):
        return self.full_path[len(self.directory_path) + 1:]
    
    def get_file_properties(self):
        return {
            "full_path": self.full_path,
            "file_name": self.get_file_name(),
            "file_size": self.get_file_size(),
            "extension": self.get_extension(),
            "is_link": self.get_is_link(),
            "relative_path": self.get_relative_path()
        }

    def __deepcopy__(self, memodict=None):
        return self


def get_porn_directory(directory_id):
    try:
        return PornDirectory.objects.get(id=int(directory_id))
    except ObjectDoesNotExist:
        return None
    except ValueError:
        return False


def get_porn_directory_info_and_content(porn_directory=None, porn_directory_id=''):
    if porn_directory is None:
        if porn_directory_id == '':
            return None
        porn_directory = get_porn_directory(porn_directory_id)
        if porn_directory is None or porn_directory is False:
            return porn_directory

    directory_info = porn_directory.serialize()
    directory_info['movies'] = get_movies_of_porn_directory(porn_directory)
    return directory_info


def get_movies_of_porn_directory(porn_directory):
    try:
        return [movie.serialize() for movie in porn_directory.movies.all()]
    except ObjectDoesNotExist:
        # Thank you Race Conditions...
        return []


def get_porn_directory_ids():
    return [s.id for s in PornDirectory.objects.only('pk')]


def get_target_porn_directory():
    return PornDirectory.objects.get(id=0)
