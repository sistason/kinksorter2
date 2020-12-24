from os import path, access, W_OK, R_OK
import argparse
import logging

from django.core.management.base import BaseCommand


from kinksorter_app.apis.kinkcom.kink_recognition import KinkRecognition
from kinksorter_app.apis.kinkcom.kink_api import KinkAPI

logger = logging.getLogger(__name__)


def argcheck_dir(string):
    if path.isdir(string) and access(string, W_OK) and access(string, R_OK):
        return path.abspath(string)
    raise argparse.ArgumentTypeError('{} is no directory or isn\'t writeable'.format(string))


class Command(BaseCommand):
    logging.basicConfig(level=logging.DEBUG)

    help = "Recognizes target movie"

    def add_arguments(self, parser):
        parser.add_argument('movie_path', type=str)

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.DEBUG)

        movie_path = options['movie_path']
        rec = KinkRecognition(KinkAPI())

        class MovieMock:
            full_path = movie_path
            file_name = path.basename(movie_path)

        shoot_id = rec.recognize(MovieMock())
        print(f"Recognized {movie_path} as shootid: {shoot_id}")
        print(f" ({rec.api.query('shoot', 'shootid', shoot_id)})")
