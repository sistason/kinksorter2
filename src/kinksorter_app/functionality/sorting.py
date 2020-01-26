import logging
import shutil
import os

from django.http import HttpResponse, JsonResponse
from django_q.tasks import async_task, Iter, result, fetch
from kinksorter_app.apis.api_router import APIS
from kinksorter_app.models import PornDirectory, Movie, CurrentTask, get_scene_from_movie
from kinksorter_app.functionality.status import get_current_task, hook_set_task_ended
from kinksorter_app.functionality.directory_handling import Leaf, get_target_porn_directory


def get_current_task_request(request):
    task = get_current_task()
    return JsonResponse(task, safe=False)


def sort_movie_into_target_request(request):
    action_ = request.GET.get('action')
    movie_id = request.GET.get('movie_id')

    movie = Movie.objects.get(id=movie_id)

    return sort_into_target(action_, movies=[movie])


def sort_into_target(action_, movies):
    if not action_ or action_ not in ['move', 'copy', 'cmd', 'list']:
        return HttpResponse('action needs to be a valid value', status=400)

    if CurrentTask.objects.count():
        return HttpResponse('Task running! Wait for completion before sorting.', status=503)

    sorter = TargetSorter(action_, movies)
    async_task(sorter.sort)

    task_ = CurrentTask(name='Sorting', progress_max=len(movies))
    task_.save()

    return HttpResponse('sorting started', status=200)


def sort_target_request(request):
    action_ = request.GET.get('action')
    if not action_ or action_ not in ['move']:
        return HttpResponse('action needs to be a valid value', status=400)

    if CurrentTask.objects.count():
        return HttpResponse('Task running! Wait for completion before sorting.', status=503)

    sorter = TargetSorter(action_)
    async_task(sorter.sort)

    task_ = CurrentTask(name='Sorting', progress_max=get_target_porn_directory().movies.count())
    task_.save()

    return HttpResponse('sorting started', status=200)


def revert_target_request(request):
    movies = PornDirectory.objects.get(id=0).movies.all()

    if CurrentTask.objects.count():
        return HttpResponse('Task running! Wait for completion before reverting.', status=503)

    task_ = CurrentTask(name='Reverting', progress_max=movies.count())
    task_.save()

    sorter = TargetSorter('')
    async_task(sorter.revert_target)

    return HttpResponse('reverting started', status=200)


class TargetSorter:
    def __init__(self, action, movies=None):
        self.action = action
        self.target_directory = get_target_porn_directory()

        self.movies = movies if movies is not None else self.target_directory.movies.all()
        self.sort_format = self.target_directory.sort_format
        # Shopping list holds a list of which movies to get of this directory
        self.movie_list = []

    def sort(self):
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
        logging.info('Sorting...')

        current_task, _ = CurrentTask.objects.get_or_create(name='Sorting')
        for movie in self.movies:
            logging.debug('Sorting movie {}...'.format(movie.file_name))

            self._sort_movie(movie)

            current_task.progress_current += 1
            current_task.save()

        if self.action == 'list':
            return self._get_shopping_list()
        if self.action == 'cmd':
            return self._get_cmd_list()

        return True

    def _get_shopping_list(self):
        return '\n'.join([from_ for (cmd, from_, target_, target_dir_) in self.movie_list])

    def _get_cmd_list(self):
        return '\n'.join(['mkdir -p {}\n{} "{}" "{}"'.format(target_dir_, cmd, from_, target_) for
                          (cmd, from_, target_, target_dir_) in self.movie_list])

    def _sort_movie(self, movie):
        if not os.path.exists(movie.full_path):
            logging.warning(' Movie-path does not exist anymore!')
            return

        scene_, new_movie_path = self._build_new_movie_path(movie)

        if self.action in ['cmd', 'list']:
            self._list_movie(movie, new_movie_path)
            return

        if os.path.exists(new_movie_path):
            # Only overwrite file when the new movie is "better" (quality)
            if not self._is_new_movie_better(movie, new_movie_path):
                logging.warning('Existing file "{}" is equal or better than new file "{}", skipping...'.format(
                    new_movie_path, movie.full_path))
                return

        self._act_movie(movie, new_movie_path)

    def _list_movie(self, movie, target_movie_path):
        existing_file = target_movie_path if os.path.exists(target_movie_path) else None

        delete = []
        for position, _, c, p, _ in enumerate(self.movie_list):
            if p == target_movie_path:
                if self._is_new_movie_better(movie, c) and self._is_new_movie_better(movie, existing_file):
                    # Mark for deletion, as this new movie is better than the one in the list
                    delete.append(position)
                else:
                    # if the movie is not better, skip adding it
                    break
        else:
            for i in delete:
                del self.movie_list[i]

            target_directory = os.path.dirname(target_movie_path)
            if os.access(movie.full_path, os.W_OK):
                self.movie_list.append(('mv', movie.full_path, target_movie_path, target_directory))
            else:
                self.movie_list.append(('cp', movie.full_path, target_movie_path, target_directory))

        return None

    def _act_movie(self, movie, target_movie_path):
        if os.path.islink(target_movie_path):
            # When replacing links, remove the link beforehand (:/$ mv a_file a_link: Error! Same file!)
            os.remove(target_movie_path)

        try:
            if self.action == 'move':
                shutil.move(movie.full_path, target_movie_path)
            elif self.action == 'copy':
                shutil.copy(movie.full_path, target_movie_path)
            else:
                return

        except os.error as e:
            logging.warning(
                'File "{}" could not be {}}! {}'.format(target_movie_path, self.action, e))
            return

    @staticmethod
    def _is_new_movie_better(movie, new_movie_path):
        # This can get arbitrarily complex (bitrate, resolution, encoding, etc)
        new_size = os.stat(new_movie_path).st_size
        old_size = movie.file_size
        return new_size > old_size

    def _build_new_movie_path(self, movie):
        scene = get_scene_from_movie(movie)
        target_base = PornDirectory.objects.get(id=0).path
        if scene:
            site_pathname = scene.get('site', {}).get('name')
            performers = ', '.join([i.get('name', 'API-Error') for i in scene.get('performers')])
            api = movie.api.name

            new_filename = self.sort_format.format(movie=movie,
                                                   scene=scene,
                                                   site_name=site_pathname,
                                                   performers=performers,
                                                   api=api)
        else:
            site_pathname = '_unsorted'
            new_filename = movie.file_name

        target_path = os.path.join(target_base, site_pathname, new_filename)

        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        return scene, target_path

    def revert_target(self):
        logging.info('Reverting"...')

        target_directory = PornDirectory.objects.get(id=0)
        current_task, _ = CurrentTask.objects.get_or_create(name='Reverting')

        for movie in self.movies:
            if movie.is_original:
                continue

            self._revert_movie(movie)

            target_directory.movies.remove(movie)
            movie.delete()

            current_task.progress_current += 1
            current_task.save()

        logging.info('Finished reverting')

    def _revert_movie(self, movie):
        original_path = movie.full_path
        scene, current_path = self._build_new_movie_path(movie)
        if os.path.exists(original_path):
            try:
                os.remove(current_path)
            except FileNotFoundError:
                pass
            return

        if not os.path.exists(current_path):
            return
        if os.path.islink(current_path):
            os.remove(current_path)
            return

        if not os.access(original_path, os.W_OK):
            logging.warning(
                'Original path is not writeable, but the movie is not there. Keeping the local (and only) copy')
            return

        os.makedirs(os.path.dirname(original_path), exist_ok=True)
        shutil.move(current_path, original_path)

        # if it's the last movie, remove the site-directory
        if not os.listdir(os.path.dirname(current_path)):
            os.rmdir(os.path.dirname(current_path))
