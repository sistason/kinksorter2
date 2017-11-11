import logging
import shutil
import os

from django.http import HttpResponse, JsonResponse
from django_q.tasks import async, Iter, result, fetch
from kinksorter.settings import TARGET_DIRECTORY_PATH
from kinksorter_app.apis.api_router import APIS
from kinksorter_app.models import TargetPornDirectory, CurrentTask, get_scene_from_movie, get_target_path
from kinksorter_app.functionality.status import get_current_task, hook_set_task_ended
from kinksorter_app.functionality.directory_handling import Leaf


def get_current_task_request(request):
    task = get_current_task()
    return JsonResponse(task, safe=False)


def sort_into_target(request):
    action_ = request.GET.get('action')

    if not action_ or action_ not in ['move', 'link', 'cmd']:
        return HttpResponse('action needs to be a valid value', status=400)

    if CurrentTask.objects.exists():
        return HttpResponse('Task running! Wait for completion before sorting.', status=503)

    sorter = TargetSorter(action=action_)
    async(sorter.sort)

    task_ = CurrentTask(name='Sorting', progress_max=TargetPornDirectory.objects.get().movies.count())
    task_.save()

    return HttpResponse('sorting started', status=200)


class TargetSorter:
    def __init__(self, action='link'):
        self.action = action
        # Shopping list holds tuple of ('action', from, target, target_dir)
        self.shopping_list = []

    def sort(self):
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
        logging.info('Sorting...')

        current_task = CurrentTask.objects.get(name='Sorting')
        for movie in TargetPornDirectory.objects.get().movies.all():
            logging.debug('Sorting movie {}...'.format(movie.file_properties.file_name))

            self._sort_movie(movie)

            current_task.progress_current += 1
            current_task.save()

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

        scene_, new_movie_path = self._build_new_movie_path(movie)

        if self.action in ['cmd', 'list']:
            self._list_movie(movie, new_movie_path)
            return

        if self.action == 'move' and os.path.islink(new_movie_path):
            # When replacing links, remove the link beforehand (:/$ mv a_file a_link: Error! Same file!)
            os.remove(new_movie_path)

        if os.path.exists(new_movie_path):
            # Only overwrite file when the new movie is "better" (quality)
            if not self._is_new_movie_better(movie, new_movie_path):
                logging.warning('Existing file "{}" is equal or better than new file "{}", skipping...'.format(
                    new_movie_path, movie.file_properties.full_path))
                return

        if self.action == 'link':
            self._link_movie(movie, new_movie_path)
        elif self.action == 'move':
            self._move_movie(movie, new_movie_path)
        else:
            logging.error('action "{}" not yet implemented!'.format(self.action))

    def _list_movie(self, movie, target_movie_path):
        existing_file = target_movie_path if os.path.exists(target_movie_path) else None

        delete = []
        for position, _, c, p, _ in enumerate(self.shopping_list):
            if p == target_movie_path:
                if self._is_new_movie_better(movie, c) and self._is_new_movie_better(movie, existing_file):
                    # Mark for deletion, as this new movie is better than the one in the list
                    delete.append(position)
                else:
                    # if the movie is not better, skip adding it
                    break
        else:
            for i in delete:
                del self.shopping_list[i]

            target_directory = os.path.dirname(target_movie_path)
            if os.access(movie.file_properties.full_path, os.W_OK):
                self.shopping_list.append(('mv', movie.file_properties.full_path, target_movie_path, target_directory))
            else:
                self.shopping_list.append(('cp', movie.file_properties.full_path, target_movie_path, target_directory))

        return None

    def _link_movie(self, movie, target_movie_path):
        if os.path.exists(target_movie_path):
            if os.path.islink(target_movie_path):
                # File has not to exist for os.symlink
                os.remove(target_movie_path)
            else:
                logging.warning(
                    'File "{}" already existed! We only link files, skipping...'.format(target_movie_path))
                return

        if self._cleanup_previously_sorted(movie, target_movie_path):
            # File already moved to new location
            return

        os.symlink(movie.file_properties.full_path, target_movie_path)
        self._save_sorted_properties(movie, target_movie_path)

    @staticmethod
    def _save_sorted_properties(movie, target_movie_path):
        movie.sorted_properties = Leaf(target_movie_path, TARGET_DIRECTORY_PATH).get_file_properties()
        movie.sorted_properties.save()
        movie.save()

    @staticmethod
    def _cleanup_previously_sorted(movie, target_movie_path):
        """
        If the movie was sorted before, delete that file if it is a link or move that file to the new position.
        Note that we cannot know if the original directory exists and if moving it back there (in case of now linking
        movies) is the right thing to do at all. The link/move distinction was only made to protect original
        directories, so if the file is already in the target directory, we can just ignore this precaution.
        Keep in mind that because of this, directories are only safe to delete if there wasn't moved anything in
        in-between!

        :param movie:
        :param target_movie_path:
        :return: True if the file was moved (skip further processing), None for continuing
        """
        if movie.sorted_properties:
            if not movie.sorted_properties.is_link:
                # was sorted before, use that file to clean up and for speed (probably same filesystem)
                shutil.move(movie.sorted_properties.full_path, target_movie_path)
                return True
            else:
                # was sorted before, remove previous file/link
                os.remove(movie.sorted_properties.full_path)
            movie.sorted_properties.delete()

    def _move_movie(self, movie, target_movie_path):
        if self._cleanup_previously_sorted(movie, target_movie_path):
            # File already moved to new location
            return

        try:
            if not os.access(movie.file_properties.full_path, os.W_OK) or \
                    any([dir_.is_read_only for dir_ in movie.porndirectory_set.all()]):
                shutil.copy(movie.file_properties.full_path, target_movie_path)
            else:
                shutil.move(movie.file_properties.full_path, target_movie_path)

            self._save_sorted_properties(movie, target_movie_path)
        except os.error:
            pass

    @staticmethod
    def _is_new_movie_better(movie, new_movie_path):
        # This can get arbitrarily complex (bitrate, resolution, encoding, etc)
        new_size = os.stat(new_movie_path).st_size
        old_size = movie.file_properties.file_size
        return new_size > old_size

    @staticmethod
    def _build_new_movie_path(movie):
        scene = get_scene_from_movie(movie)
        target_path = get_target_path(movie, scene)

        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        return scene, target_path

    def revert(self):
        logging.info('Reverting"...')

        current_task = CurrentTask.objects.get(name='Reverting')

        for movie in TargetPornDirectory.objects.get().movies.all():
            self._revert_movie(movie)

            current_task.progress_current += 1
            current_task.save()

        logging.info('Finished reverting')

    def _revert_movie(self, movie):
        original_path = movie.file_properties.full_path
        scene, current_path = self._build_new_movie_path(movie)
        if os.path.exists(original_path):
            os.remove(current_path)
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


def revert_target(request):
    if CurrentTask.objects.exist():
        return HttpResponse('Task running! Wait for completion before reverting.', status=503)

    task_ = CurrentTask(name='Reverting', progress_max=TargetPornDirectory.objects.get().movies.count())
    task_.save()

    sorter = TargetSorter()
    async(sorter.revert)

    return HttpResponse('reverting started', status=200)


