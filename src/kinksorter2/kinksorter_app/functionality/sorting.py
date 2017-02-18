import logging
import os

from kinksorter2.kinksorter_app.models import Storage
from kinksorter2.kinksorter.settings import BASE_DIR

def sort_all():
    logging.info('Sorting everything...')

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

