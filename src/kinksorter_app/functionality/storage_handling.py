import subprocess
import logging
import os

from django_q.tasks import async
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.serializers import serialize

from kinksorter_app.models import Storage, Movie, FileProperties, MainStorage
from kinksorter_app.apis.api_router import get_correct_api, APIS


class StorageHandler:
    scanner = None
    storage = None

    def __init__(self, storage_input, name='', read_only=False):
        if type(storage_input) == str:
            if not os.path.exists(storage_input) or \
               not read_only and not os.access(storage_input, os.W_OK):
                return

            if Storage.objects.filter(path=os.path.abspath(storage_input)).exists() \
               or name and Storage.objects.filter(name=name).exists():
                return

            new_storage = Storage(path=os.path.abspath(storage_input), name=name, read_only=read_only)
            new_storage.save()

            self.storage = new_storage
        else:
            try:
                self.storage = Storage.objects.get(id=storage_input)
            except ObjectDoesNotExist:
                return

        self.scanner = MovieScanner(self.storage, APIS)

    def scan(self):
        if self.storage is not None:
            logging.basicConfig(format='%(message)s',
                                level=logging.DEBUG)
            self.scanner.scan()

    def delete(self):
        if self.storage is not None:
            for movie in self.storage.movies.all():
                movie.delete()
            self.storage.delete()

    def __bool__(self):
        return self.storage is not None


class MovieScanner:
    def __init__(self, storage, apis):
        self.apis = apis
        self.storage = storage
        self.directory_tree = DirectoryTree(storage.path)

    def scan(self):
        self._get_listing(self.directory_tree, recursion_depth=5)
        self._scan_tree(self.directory_tree)

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
        for leaf in tree.leafs:
            logging.debug('Scanning file {}...'.format(leaf.full_path[-100:]))
            if leaf.is_writeable() and leaf.is_video_file():
                logging.debug('  Adding movie {}...'.format(leaf.full_path[-100:]))
                async(self.add_movie, leaf, tree)

        for next_tree in tree.nodes:
            self._scan_tree(next_tree)

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

        scene_properties = api.recognize(movie)
        if scene_properties:
            movie.scene_properties = scene_properties
        movie.save()

        self.storage.movies.add(movie)
        print('ADDED MOVIE {}...'.format(movie.scene_properties))


class DirectoryTree:
    def __init__(self, path, prev=None, api=None):
        self.leafs = []
        self.nodes = []

        self.prev = prev
        self.path = path
        self.api = api


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


def get_storage(storage_id):
    try:
        return Storage.objects.get(id=int(storage_id))
    except ObjectDoesNotExist:
        return None


def get_main_storage():
    storage = None
    try:
        storage = MainStorage.objects.get_or_create()[0]
    except MultipleObjectsReturned:
        for stor_ in MainStorage.objects.order_by('movies__count'):
            if storage is None:
                storage = stor_
            else:
                stor_.delete()

    return get_main_storage_data(storage)


def get_main_storage_data(storage):
    return {'storage_path': storage.path,
            'storage_date': storage.date_added,
            'movies': get_movies_of_storage(storage)
            }


def change_storage_name(storage_id, new_name):
    storage = get_storage(storage_id)
    if storage:
        storage.name = new_name
        storage.save()
        return True


def get_movies_of_storage(storage):
    rows = []
    for movie in storage.movies.all():
        status = 'okay'
        if not movie.scene_properties:
            scene = {}
            status = 'unrecognized'
        else:
            try:
                api = APIS.get(movie.api, APIS.get('default'))
                model = api.get_correct_model()
                scene = model.objects.get(shootid=movie.scene_properties).serialize()
            except Exception as e:
                print('Here HAS to fail something at some point...', e)
                print('API: ', api)
                print('Model: ', model)
                print('Manager: ', model.objects)
                print('scene_id: ', movie.scene_properties)
                print('scene: ', model.objects.filter(shootid=movie.scene_properties))


        #duplicate = MainStorage.objects.get().movies.filter(movie_id=movie.id)
        if status == 'okay' and movie.mainstorage_set.exists():
            status = 'duplicate'

        new_storage = movie.storage_set.get()
        movie_row = {'storage_name': new_storage.name,
                     'storage_id': new_storage.id,
                     'movie_id': movie.id,
                     'api': movie.api,
                     'full_path': movie.file_properties.full_path,
                     'watch_scene': 'file:/{}'.format(movie.file_properties.full_path),
                     'scene_title': scene.get('title'),
                     'scene_site': scene.get('site', {}).get('name'),
                     'scene_date': scene.get('date'),
                     'scene_id': scene.get('shootid'),
                     'status': status
                     }

        rows.append(movie_row)

    return rows


def get_new_storage_data(storage):
    return get_movies_of_storage(storage) + [{'storage_name': storage.name,
                                              'storage_id': storage.id,
                                              'storage_movies_count': storage.movies.count(),
                                              'storage_path': storage.path,
                                              'storage_read_only': storage.read_only,
                                              'storage_date': storage.date_added,
                                              'type': 'storage'
                                             }]


def get_storage_ids():
    return [s.id for s in Storage.objects.only('pk')]
