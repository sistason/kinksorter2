from django.core.exceptions import ObjectDoesNotExist

from kinksorter_app.apis.api_router import APIS
from kinksorter_app.models import Storage, Movie, FileProperties


class RecognitionHandler:

    def __init__(self, movie_id):
        try:
            self.movie = Movie.objects.get(id=movie_id)
            self.api = APIS.get(self.movie.api) if self.movie.api in APIS else APIS.get('Default')
        except ObjectDoesNotExist:
            self.movie = None
            self.api = None

    def recognize(self, new_name='', new_sid=0):
        self.api.recognize(self.movie, override_name=new_name, override_sid=new_sid)

        if self.movie.scene_properties != 0:
            self.movie.save()
            return True