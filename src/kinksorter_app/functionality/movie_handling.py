from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from kinksorter_app.apis.api_router import APIS
from kinksorter_app.models import Storage, Movie, FileProperties, MainStorage


class RecognitionHandler:

    def __init__(self, movie_id):
        try:
            self.movie = Movie.objects.get(id=movie_id)
            self.api = APIS.get(self.movie.api) if self.movie.api in APIS else APIS.get('Default')
        except ObjectDoesNotExist:
            self.movie = None
            self.api = None

    def recognize(self, new_name='', new_sid=0):
        scene_properties = self.api.recognize(self.movie, override_name=new_name, override_sid=new_sid)

        if scene_properties != 0 and scene_properties is not None:
            self.movie.scene_properties = scene_properties
            self.movie.save()
            return self.movie


def delete_movie(movie_id):
    return bool([movie.delete() for movie in Movie.objects.filter(id=movie_id)])


def remove_movie_from_main(movie_id):
    try:
        movie = get_movie(movie_id)
        mainstorage = MainStorage.objects.get()
        if movie:
            return mainstorage.movies.remove(movie)
    except (ObjectDoesNotExist, ValueError):
        return None


def merge_movie(movie_id):
    movie = get_movie(movie_id)
    if movie is not None:
        MainStorage.objects.get().movies.add(movie)
        return movie


def get_movie(movie_id):
    try:
        return Movie.objects.get(id=int(movie_id))
    except (ObjectDoesNotExist, ValueError):
        return None
