from os import path, access, W_OK, R_OK
import argparse
import logging

from django.core.management.base import BaseCommand, CommandError

from kinksorter_app.functionality.movie_handling import merge_movie, recognize_movie
from kinksorter_app.models import Movie, PornDirectory
from kinksorter_app.functionality.directory_handling import PornDirectoryHandler, get_target_porn_directory

from kinksorter_app.functionality.sorting import TargetSorter

logger = logging.getLogger(__name__)


def argcheck_dir(string):
    if path.isdir(string) and access(string, W_OK) and access(string, R_OK):
        return path.abspath(string)
    raise argparse.ArgumentTypeError('{} is no directory or isn\'t writeable'.format(string))


class Command(BaseCommand):
    logging.basicConfig(level=logging.DEBUG)

    help = "Syncs a source directory into a destination directory"

    def add_arguments(self, parser):
        parser.add_argument('src_directory', type=argcheck_dir)
        parser.add_argument('dst_directory', type=argcheck_dir)

    def handle(self, *args, **options):
        src_dir = options['src_directory']
        dst_dir = options['dst_directory']

        logger.info("Start")

        if PornDirectory.objects.filter(id=0).exists():
            dst_handler = PornDirectoryHandler(0)
        else:
            dst_handler = PornDirectoryHandler(None, init_path=dst_dir, name="dest", id_=0)
            dst_handler.scan()  # only scan initially, since the merged files get added to the db

        if PornDirectory.objects.filter(path=src_dir).exists():
            PornDirectory.objects.delete(path=src_dir)  # don't keep the src directory, to force resyncs
            src_handler = PornDirectoryHandler(None, init_path=src_dir, name="src")
        else:
            src_handler = PornDirectoryHandler(None, init_path=src_dir, name="src")

        src_handler.scan()

        # TODO: Why is the directory empty in a docker-container with foreign db?
        for movie in src_handler.directory.movies.all():
            if not movie.scene_id:
                recognize_movie(movie, None, want_be_sure=True)
                if not movie.scene_id:
                    # if it was not recognized during first run, recognize with extensive=True again
                    recognize_movie(movie, None, extensive=True, want_be_sure=True)
            if not dst_handler.directory.movies.filter(scene_id=movie.scene_id).exists():
                merge_movie(movie.id)

        # create listing
        "filename + dir | cv md nr | sure"
        format_string = "{name:} , {}"
        with open('current_sorting_review.csv', "w") as f:
            for movie in dst_handler.directory.movies.all():

                logging.info()

        ts = TargetSorter("move", list(dst_handler.directory.movies.all()))
        ts.sort()



