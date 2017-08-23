import subprocess
import logging
import copy
import os

from django_q.tasks import async
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.serializers import serialize

from kinksorter.settings import BASE_DIR
from kinksorter_app.models import PornDirectory, Movie, FileProperties, TargetPornDirectory
from kinksorter_app.apis.api_router import get_correct_api, APIS
from kinksorter_app.functionality.movie_handling import recognize_movie, recognize_multiple


class PornDirectoryHandler:
    scanner = None
    directory = None

    def __init__(self, porn_directory, name='', read_only=False, init_path=None):
        if porn_directory is None and init_path is not None:
            if not os.path.exists(init_path) or \
               not read_only and not os.access(init_path, os.W_OK):
                return

            if PornDirectory.objects.filter(path=os.path.abspath(init_path)).exists() \
               or name and PornDirectory.objects.filter(name=name).exists():
                return

            new_porn_dir = PornDirectory(path=os.path.abspath(init_path), name=name, read_only=read_only)
            new_porn_dir.save()

            self.directory = new_porn_dir
            self.link_porn_directory()
        else:
            self.directory = get_porn_directory(porn_directory)

        self.scanner = MovieScanner(self.directory, APIS)

    def link_porn_directory(self):
        link_path = os.path.join(BASE_DIR, 'kinksorter', 'static', str(self.directory.id))
        if os.path.exists(link_path):
            os.unlink(link_path)

        os.symlink(self.directory.path, link_path)

    def reset(self):
        for movie in self.directory.movies.all():
            movie.delete()
        self.directory.save()

        return self.scan()

    def rerecognize(self):
        target_directory = get_target_porn_directory()
        unrecognized_movies = []
        for movie in self.directory.movies.all():
            movie.scene_properties = 0
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

            link_path = os.path.join(BASE_DIR, 'kinksorter', 'static', str(self.directory.id))
            try:
                os.unlink(link_path)
            except os.error:
                pass

    def __bool__(self):
        return self.directory is not None


class MovieScanner:
    def __init__(self, porn_directory, apis):
        self.apis = apis
        self.porn_directory = porn_directory
        self.directory_tree = DirectoryTree(porn_directory.path)

    def scan(self):
        self._get_listing(self.directory_tree, recursion_depth=5)
        return async(self._scan_tree, self.directory_tree)

    def _get_listing(self, tree, recursion_depth=0):
        recursion_depth -= 1
        for entry in os.scandir(tree.path):
            try:
                if entry.is_dir() and recursion_depth > 0:
                    api = tree.api if tree.api else get_correct_api(entry.name, self.apis)
                    new_tree = DirectoryTree(entry.path, prev=tree, api=api)
                    tree.nodes.append(new_tree)
                    name_ = api.name if api else '<None>'
                    logging.info('Scanning directory (API: {}) {}...'.format(name_, entry.path))
                    self._get_listing(new_tree, recursion_depth)

                if entry.is_file() or entry.is_symlink():
                    tree.leafs.append(Leaf(entry.path))
            except OSError:
                pass

    def _scan_tree(self, tree):
        logging.basicConfig(format='%(message)s',
                            level=logging.DEBUG)
        for leaf in tree.leafs:
            logging.debug('Scanning file {}...'.format(leaf.full_path[-100:]))
            if leaf.is_writeable() and leaf.is_video_file():
                logging.debug('  Adding movie {}...'.format(leaf.full_path[-100:]))
                self.add_movie(leaf, tree)

        for next_tree in tree.nodes:
            async(self._scan_tree, next_tree)

    def add_movie(self, leaf, tree):
        api = tree.api if tree.api else self.apis.get('default', None)
        if api is None:
            logging.debug('    No API.')
            return

        if Movie.objects.filter(file_properties__full_path=leaf.full_path).exists():
            logging.debug('    Duplicate movie.')
            return

        relative_path = leaf.full_path[len(self.directory_tree.path):]
        file_properties = FileProperties(full_path=leaf.full_path,
                                         file_name=leaf.get_file_name(),
                                         file_size=leaf.get_file_size(),
                                         extension=leaf.get_extension(),
                                         relative_path=relative_path)
        file_properties.save()

        movie = Movie(file_properties=file_properties, api=api.name)
        movie.save()

        recognize_movie(movie, None, api=api)

        self.porn_directory.movies.add(movie)
        logging.info('ADDED MOVIE {}...'.format(movie.scene_properties))

    def __deepcopy__(self, memodict=None):
        return self


class DirectoryTree:

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
    def __init__(self, full_path):
        self.full_path = full_path

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

    def __deepcopy__(self, memodict=None):
        return self


def get_porn_directory(directory_id):
    try:
        return PornDirectory.objects.get(id=int(directory_id))
    except ObjectDoesNotExist:
        return None
    except ValueError:
        return False


def get_target_porn_directory():
    try:
        return TargetPornDirectory.objects.get_or_create()[0]
    except MultipleObjectsReturned:
        # Race Condition only
        return


def get_porn_directory_info_and_content(porn_directory=None, porn_directory_id=''):
    if porn_directory is None:
        if porn_directory_id == '':
            return None
        porn_directory = get_porn_directory(porn_directory_id)
        if porn_directory is None or porn_directory is False:
            return porn_directory

    return [porn_directory.serialize()] + get_movies_of_directory(porn_directory)


def get_movies_of_porn_directory(porn_directory):
    return [movie.serialize() for movie in porn_directory.movies.all()]


def get_porn_directory_ids():
    return [s.id for s in PornDirectory.objects.only('pk')]
