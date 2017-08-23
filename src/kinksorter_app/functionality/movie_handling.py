import logging
from django.core.exceptions import ObjectDoesNotExist

from django_q.tasks import async, Iter, result, fetch
from kinksorter_app.apis.api_router import APIS

from kinksorter_app.models import Movie, FileProperties, PornDirectory


def recognize_multiple(movie_ids, movies=None, wait_for_finish=True):
    tasks_ = []
    if movie_ids:
        for movie_id in movie_ids:
            tasks_.append(async(recognize_movie, None, movie_id))
    elif movies is not None:
        for movie in movies:
            tasks_.append(async(recognize_movie, movie, None))

    if not wait_for_finish:
        return

    recognized = []
    for task_id in tasks_:
        res = fetch(task_id, wait=2000)
        if res is not None and res.result is not None:
            recognized.append(res.result.serialize())

    """
    async_ = Iter(recognize_movie)
    [async_.append(None, movie_id) for movie_id in movie_ids]
    async_.run()

    recognized_task = async_.fetch(wait=2000)
    print(recognized_task)
    if recognized_task is not None:
        print([rec for rec in recognized_task.result])
        return [rec.serialize() for rec in recognized_task.result if rec is not None]"""
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
        print('No movie for recognition passed!')
        return

    if api is None:
        api = APIS.get(movie.api) if movie.api in APIS else APIS.get('Default')

    scene_properties = api.recognize(movie, override_name=new_name, override_sid=new_sid)
    if scene_properties is not None and scene_properties != 0:
        movie.scene_properties = scene_properties
        movie.save()
        return movie


def delete_movie(movie_id):
    return bool([movie.delete() for movie in Movie.objects.filter(id=movie_id)])


def remove_movie_from_target(movie_id, target_porn_directory):
    try:
        movie = get_movie(movie_id)
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
