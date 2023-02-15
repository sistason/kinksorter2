from django.db import models
import django.utils.timezone
import datetime
from os import path, symlink, remove
import logging

from kinksorter.settings import DEBUG_SFW, STATIC_LINKED_DIRECTORIES, DIRECTORY_LINKS
from kinksorter_app.apis.api_router import APIS


def get_scene_from_movie(movie):
    if movie.scene_id:
        api = APIS.get(movie.api, APIS.get('default'))
        if api:
            scenes = api.query('shoot', 'shootid', movie.scene_id)
            if len(scenes) > 1:
                logging.warning('Multiple scenes for shootid {} found! ({})'.format(movie.scene_id, scenes))
            scene = scenes[0]
            if scene.get('exists'):
                return scene
    return {}


class Movie(models.Model):
    api = models.CharField(max_length=50, null=True)
    # scene_properties contains an id to find the properties again with the specified API
    scene_id = models.IntegerField(default=0)

    full_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=200)
    file_size = models.IntegerField()
    extension = models.CharField(max_length=10)
    relative_path = models.CharField(max_length=300)
    is_link = models.BooleanField(default=False)
    from_directory = models.IntegerField(default=0)

    def serialize(self):
        scene = get_scene_from_movie(self)
        porn_directory = self.porndirectory_set.get()

        status = 'done' if self.from_directory == 0 else 'okay'

        if porn_directory.id == 0:
            if not scene:
                status = 'unrecognized'
        else:
            # is duplicate if unrecognized, is not the original, and name exists in Target
            if not scene:
                if PornDirectory.objects.get(id=0).movies.filter(relative_path=self.relative_path).exists():
                    status = 'duplicate'
                else:
                    status = 'unrecognized'

            # is duplicate if recognized, is not the original, and id exists in Target
            elif PornDirectory.objects.get(id=0).movies.filter(scene_id=self.scene_id).exists():
                status = 'duplicate'

        return {
                'directory_id': porn_directory.id,
                'directory_name': porn_directory.name if self.from_directory else '',
                'type': 'movie',
                'movie_id': self.id,
                'api': '' if DEBUG_SFW else self.api,
                'full_path': self.full_path,
                'title': '' if DEBUG_SFW else (scene.get('title') if 'title' in scene else self.file_name),
                'scene_site': '' if DEBUG_SFW else scene.get('site', {}).get('name'),
                'scene_date': scene.get('date'),
                'scene_id': scene.get('shootid'),
                'status': status,
        }

    def get_video_path(self):
        return path.join(STATIC_LINKED_DIRECTORIES, str(self.porndirectory_set.get().id), str(self.relative_path))


class PornDirectory(models.Model):
    name = models.CharField(max_length=100, default='<PornDirectory>')
    path = models.CharField(max_length=500)
    date_added = models.DateTimeField(default=datetime.datetime.now)
    movies = models.ManyToManyField(Movie)
    sort_format = models.CharField(max_length=100, default="{title} [{shootid}]{extension}")

    def serialize(self):
        return {
            'porn_directory_name': self.name,
            'porn_directory_path': path.realpath(self.path),
            'porn_directory_date': self.date_added,
            'porn_directory_id': self.id,
            'porn_directory_movies_count': self.movies.count(),
        }

    def create_link_for_video(self):
        link_path = path.join(DIRECTORY_LINKS, str(self.id))
        if path.exists(link_path):
            if path.islink(link_path):
                remove(link_path)
            else:
                logging.error('Cannot relink directory "{}" to {}, there is something there!'.format(self.path, link_path))
                return

        # TODO: Why does this break in docker???
        symlink(self.path, link_path)

    def validate_sort_format(self, fmt):
        return


class CurrentTask(models.Model):
    name = models.CharField(max_length=200)
    started = models.DateTimeField(default=django.utils.timezone.now)
    ended = models.BooleanField(default=False)
    progress_max = models.IntegerField(default=0)
    progress_current = models.IntegerField(default=0)


