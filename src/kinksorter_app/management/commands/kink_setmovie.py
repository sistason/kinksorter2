import logging

from django.core.management.base import BaseCommand
from kinksorter_app.models import PornDirectory


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    logging.basicConfig(level=logging.DEBUG)

    help = "Manually sets shootid for target movie"

    def add_arguments(self, parser):
        parser.add_argument('movie_path', type=str)
        parser.add_argument('shoot_id', type=int)

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.DEBUG)

        movie_path = options['movie_path']
        shoot_id = options['shoot_id']

        for directory in PornDirectory.objects.all():
            for movie in directory.movies.filter(full_path=movie_path):
                logger.info(f"Set shootid for the movie in directory {directory.path}")
                movie.scene_id = shoot_id
                movie.save()
