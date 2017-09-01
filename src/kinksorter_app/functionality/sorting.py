import logging
import os

from django.http import HttpResponse, JsonResponse
from kinksorter_app.functionality.status import CURRENT_TASK


def sort_into_target(request):
    move_ = request.GET.get('move')
    print(move_)
    if not move_ or move_ not in ['true', 'false']:
        return HttpResponse('move needs to be boolean', status=400)

    if CURRENT_TASK:
        return HttpResponse('Task running! Wait for completion before sorting.', status=503)
    CURRENT_TASK.set('Sorting by {}'.format('Move' if move_ else 'Link'), None, None)

    return HttpResponse('nope', status=500)


    """
    new_storage_path = os.path.join(BASE_DIR, '../../..')
    for storage in Storage.objects.all():
        storage



    for old_movie_path, movie in self.database.movies.items():
        logging.debug('Sorting movie {}...'.format(old_movie_path))
        if not os.path.exists(old_movie_path):
            continue

        new_movie_path = self._build_new_movie_path(movie, new_storage_path)

        if not self._check_duplicate(movie, new_movie_path, old_movie_path):
            self._move_movie(old_movie_path, new_movie_path)
            self._cleanup_old_movie(old_movie_path)
    """


def get_current_task(request):
    return JsonResponse(CURRENT_TASK.to_dict())

