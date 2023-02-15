from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from django_q.tasks import async_task, fetch
from kinksorter_app.apis.api_router import APIS
from kinksorter_app.models import Movie, PornDirectory, CurrentTask
from kinksorter_app.functionality.status import hook_set_task_ended

import logging
logger = logging.getLogger(__name__)


def recognize_multiple(movie_ids, movies=None, wait_for_finish=True):
    tasks_ = []

    subtasks_ = len(movie_ids) if movie_ids else len(movies) if movies is not None else 0
    if settings.USE_ASYNC:
        current_task, _ = CurrentTask.objects.get_or_create(name='Recognizing')
        current_task.progress_max += subtasks_
        current_task.save()

    if movie_ids:
        for movie_id in movie_ids:
            if settings.USE_ASYNC:
                task_id = async_task(recognize_movie, None, movie_id, hook=lambda f: hook_set_task_ended(f, name='Recognizing'))
                tasks_.append(task_id)
            else:
                tasks_.append(recognize_movie(None, movie_id))
    elif movies is not None:
        for movie in movies:
            if settings.USE_ASYNC:
                task_id = async_task(recognize_movie, movie, None, hook=lambda f: hook_set_task_ended(f, name='Recognizing'))
                tasks_.append(task_id)
            else:
                tasks_.append(recognize_movie(movie, None))

    if not settings.USE_ASYNC:
        return tasks_

    if not wait_for_finish:
        return

    recognized = []
    for task_id in tasks_:
        res = fetch(task_id, wait=2000)
        if res is not None and res.result is not None:
            recognized.append(res.result.serialize())

    return recognized


def recognize_movie(movie, movie_id, new_name='', new_sid=0, api=None, extensive=False, want_be_sure=False):
    """ Runs recognition on the supplied movie, with override-arguments if passed

    This method will usually be used to run on the django-q cluster. For this reason,
    the method uses print() and does some imports/arguments implicitly."""

    if movie is not None:
        movie = movie
    elif movie_id is not None:
        try:
            movie = Movie.objects.get(id=movie_id)
        except ObjectDoesNotExist:
            pass

    if movie is None:
        logger.error('No movie for recognition passed!')
        return

    if api is None:
        api = APIS.get(movie.api) if movie.api in APIS else APIS.get('Default')

    movie.scene_id = 0
    movie.save()

    scene_id = api.recognize(movie, override_name=new_name, override_sid=new_sid,
                             extensive=extensive, want_be_sure=want_be_sure)
    if scene_id:
        movie.scene_id = scene_id
        movie.save()
        return movie


def delete_movie(movie_id):
    return bool([movie.delete() for movie in Movie.objects.filter(id=movie_id)])


def remove_movie_from_target(movie_id):
    try:
        movie = get_movie(movie_id)
        if movie:
            target_porn_directory = PornDirectory.objects.get(id=0)
            return target_porn_directory.movies.remove(movie)
    except (ObjectDoesNotExist, ValueError):
        return None


def merge_movie(movie):
    if type(movie) is int:
        movie = get_movie(movie)

    if movie is not None:
        duplicate_movie = Movie(api=movie.api, scene_id=movie.scene_id, full_path=movie.full_path,
                                file_name=movie.file_name, file_size=movie.file_size, extension=movie.extension,
                                relative_path=movie.relative_path, is_link=movie.is_link,
                                from_directory=movie.porndirectory_set.get().id)
        duplicate_movie.save()
        target_porn_directory = PornDirectory.objects.get(id=0)
        target_porn_directory.movies.add(duplicate_movie)
        return movie


def get_movie(movie_id):
    try:
        return Movie.objects.get(id=int(movie_id))
    except (ObjectDoesNotExist, ValueError):
        return None
