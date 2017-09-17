import logging
import shutil
import os

from django.http import HttpResponse, JsonResponse
from django_q.tasks import async, Iter, result, fetch
from kinksorter_app.apis.api_router import APIS
from kinksorter_app.models import TargetPornDirectory, CurrentTask
from kinksorter_app.functionality.status import get_current_task, hook_set_task_ended
from kinksorter.settings import TARGET_DIRECTORY_PATH


def get_current_task_request(request):
    task = get_current_task()
    return JsonResponse(task, safe=False)


def sort_into_target(request):
    action_ = request.GET.get('action')

    if not action_ or action_ not in ['move', 'link', 'cmd']:
        return HttpResponse('action needs to be a valid value', status=400)

    if CurrentTask.objects.exist():
        return HttpResponse('Task running! Wait for completion before sorting.', status=503)

    sorter = TargetSorter(action_)
    async(sorter.sort)

    task_ = CurrentTask(name='Sorting', task_id=0, subtasks=TargetPornDirectory.objects.get().movies.count())
    task_.save()

    return HttpResponse('sorting started', status=200)


class TargetSorter:
    def __init__(self, action):
        self.action = action
        # Shopping list holds tuple of ('action', from, target, target_dir)
        self.shopping_list = []

    def sort(self):
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        logging.info('Sorting...')

        for movie in TargetPornDirectory.objects.get().movies.all():
            logging.debug('Sorting movie {}...'.format(movie.file_properties.file_name))

            task_ = CurrentTask(name='Sorting movie {}'.format(movie.file_properties.file_name), task_id=0)
            task_.save()

            self._sort_movie(movie)

            task_.ended = True
            task_.save()

        if self.action == 'list':
            return self._get_shopping_list()
        if self.action == 'cmd':
            return self._get_cmd_list()

        return True

    def _get_shopping_list(self):
        return '\n'.join([from_ for (cmd, from_, target_, target_dir_) in self.shopping_list])

    def _get_cmd_list(self):
        return '\n'.join(['mkdir -p {}\n{} "{}" "{}"'.format(target_dir_, cmd, from_, target_) for
                          (cmd, from_, target_, target_dir_) in self.shopping_list])

    def _sort_movie(self, movie):
        if not os.path.exists(movie.file_properties.full_path):
            logging.warning(' Movie-path does not exist anymore!')
            return

        new_movie_path = self._build_new_movie_path(movie)

        if self.action == 'move' and os.path.islink(new_movie_path):
            # When replacing links, remove the link beforehand (:/$ mv a_file a_link: Error! Same file!)
            os.remove(new_movie_path)

        if os.path.exists(new_movie_path):
            # Only overwrite file when the new movie is "better" (quality)
            if not self._is_new_movie_better(new_movie_path, movie.file_properties.full_path):
                logging.warning('Existing file "{}" is equal or better than new file "{}", skipping...'.format(
                    new_movie_path, movie.file_properties.full_path))
                return

        if self.action == 'link':
            self._link_movie(movie, new_movie_path)
        elif self.action == 'move':
            self._move_movie(movie, new_movie_path)
        elif self.action in ['cmd', 'list']:
            self.shopping_list.append(self._list_movie(movie, new_movie_path))
        else:
            logging.error('action "{}" not yet implemented!'.format(self.action))

    @staticmethod
    def _list_movie(movie, target_movie_path):
        target_directory = os.path.dirname(target_movie_path)
        if os.access(movie.file_properties.full_path, os.W_OK):
            return 'mv', movie.file_properties.full_path, target_movie_path, target_directory
        else:
            return 'cp', movie.file_properties.full_path, target_movie_path, target_directory

    @staticmethod
    def _link_movie(movie, target_movie_path):
        if os.path.exists(target_movie_path):
            if os.path.islink(target_movie_path):
                # File has not to exist for os.symlink
                os.remove(target_movie_path)
            else:
                logging.warning(
                    'File "{}" already existed! We only link files, skipping...'.format(target_movie_path))
                return

        os.symlink(movie.file_properties.full_path, target_movie_path)

    @staticmethod
    def _move_movie(movie, target_movie_path):
        if not os.access(movie.file_properties.full_path, os.W_OK) or \
                any([dir_.is_read_only for dir_ in movie.porndirectory_set.all()]):
            shutil.copy(movie.file_properties.full_path, target_movie_path)
        else:
            shutil.move(movie.file_properties.full_path, target_movie_path)

    @staticmethod
    def _is_new_movie_better(old_movie_path, new_movie_path):
        # This can get arbitrarily complex (bitrate, resolution, encoding, etc)
        new_size = os.stat(new_movie_path).st_size
        old_size = os.stat(old_movie_path).st_size
        return new_size > old_size

    @staticmethod
    def _build_new_movie_path(movie):
        scene = None
        if movie.scene_properties:
            api = APIS.get(movie.api, APIS.get('default'))
            if api:
                scene = api.query('shoot', 'shootid', movie.scene_properties)
                if len(scene) > 1:
                    logging.warning('Multiple scenes for shootid {} found! ({})'.format(movie.scene_properties, scene))
                scene = scene[0]
                if not scene.get('exists'):
                    scene = None

        site_pathname = scene.get('site', {}).get('name') if scene else '_unsorted'

        new_site_path = os.path.join(TARGET_DIRECTORY_PATH, site_pathname)
        os.makedirs(new_site_path, exist_ok=True)

        return os.path.join(new_site_path, movie.file_properties.file_name)


def revert_target(request):
    if CurrentTask.objects.exist():
        return HttpResponse('Task running! Wait for completion before reverting.', status=503)

    task_id = async(_revert, hook=hook_set_task_ended)

    task_ = CurrentTask(name='Reverting', task_id=task_id, long=True)
    task_.save()

    return HttpResponse('reverting started', status=200)


def _revert():
    logging.info('Reverting"...')

    n = len(self.database.movies)
    for i, (path_, movie) in enumerate(self.database.movies.items()):
        if os.path.exists(path_) and os.path.isfile(path_):
            continue
        if os.path.exists(path_):
            os.remove(path_)

        movie_name = str(movie)
        # TODO: subdirectories
        if movie.scene_properties.is_filled():
            site_ = movie.scene_properties.site
        else:
            site_ = os.path.join(self.UNSORTED_DIRECTORY_NAME, movie.file_properties.subdirectory_path)

        sorted_site_path = os.path.join(sorted_path, site_)
        sorted_movie_path = os.path.join(sorted_site_path, movie_name)
        if os.path.exists(sorted_movie_path):
            os.makedirs(os.path.dirname(path_), exist_ok=True)
            shutil.move(sorted_movie_path, path_)

            if not os.listdir(sorted_site_path):
                os.rmdir(sorted_site_path)

        logging.debug('Reverted movie {}/{}:\n\t\t\t{} ->\n\t\t\t {}... '.format(i + 1, n, movie_name, path_))

    if not os.listdir(sorted_path):
        # Normally, the .kinksorter_db stays there, to not punch holes in the reversion.
        os.rmdir(sorted_path)

    logging.info('Finished reversion')