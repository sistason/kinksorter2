from django.core.exceptions import ObjectDoesNotExist

from django_q.tasks import async, fetch
from kinksorter_app.apis.api_router import APIS
from kinksorter_app.models import Movie, FileProperties, PornDirectory, CurrentTask, TargetPornDirectory
from kinksorter_app.functionality.status import hook_set_task_ended

import logging
logger = logging.getLogger(__name__)


def recognize_multiple(movie_ids, movies=None, wait_for_finish=True):
    tasks_ = []

    subtasks_ = len(movie_ids) if movie_ids else len(movies) if movies is not None else 0
    current_task, _ = CurrentTask.objects.get_or_create(name='Recognizing')
    current_task.progress_max += subtasks_
    current_task.save()

    if movie_ids:
        for movie_id in movie_ids:
            task_id = async(recognize_movie, None, movie_id, hook=lambda f: hook_set_task_ended(f, name='Recognizing'))
            tasks_.append(task_id)
    elif movies is not None:
        for movie in movies:
            task_id = async(recognize_movie, movie, None, hook=lambda f: hook_set_task_ended(f, name='Recognizing'))
            tasks_.append(task_id)

    if not wait_for_finish:
        return

    recognized = []
    for task_id in tasks_:
        res = fetch(task_id, wait=2000)
        if res is not None and res.result is not None:
            recognized.append(res.result.serialize())

    return recognized


def recognize_movie(movie, movie_id, new_name='', new_sid=0, api=None):
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

    movie.scene_properties = 0
    movie.save()

    scene_properties = api.recognize(movie, override_name=new_name, override_sid=new_sid)
    if scene_properties is not None and scene_properties != 0:
        movie.scene_properties = scene_properties
        movie.save()
        return movie


def delete_movie(movie_id):
    return bool([movie.delete() for movie in Movie.objects.filter(id=movie_id)])


def remove_movie_from_target(movie_id):
    try:
        movie = get_movie(movie_id)
        target_porn_directory = TargetPornDirectory.objects.get()
        if movie and target_porn_directory:
            return target_porn_directory.movies.remove(movie)
    except (ObjectDoesNotExist, ValueError):
        return None


def merge_movie(movie_id, target_porn_directory):
    movie = get_movie(movie_id)
    if movie is not None and target_porn_directory is not None:
        target_porn_directory.movies.add(movie)
        return movie


def get_movie(movie_id):
    try:
        return Movie.objects.get(id=int(movie_id))
    except (ObjectDoesNotExist, ValueError):
        return None
