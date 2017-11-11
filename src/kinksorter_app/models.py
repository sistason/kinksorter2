from django.db import models
import django.utils.timezone
import datetime
from os import path
import logging

from kinksorter.settings import BASE_DIR, DEBUG_SFW, DIRECTORY_STATIC_LINK_NAME, STATIC_URL, TARGET_DIRECTORY_PATH
from kinksorter_app.apis.api_router import APIS


class FileProperties(models.Model):
    full_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=200)
    file_size = models.IntegerField()
    extension = models.CharField(max_length=10)
    relative_path = models.CharField(max_length=300)
    is_link = models.BooleanField(default=False)


def get_scene_from_movie(movie):
    if movie.scene_properties:
        api = APIS.get(movie.api, APIS.get('default'))
        if api:
            scenes = api.query('shoot', 'shootid', movie.scene_properties)
            if len(scenes) > 1:
                logging.warning('Multiple scenes for shootid {} found! ({})'.format(movie.scene_properties, scenes))
            scene = scenes[0]
            if scene.get('exists'):
                return scene
    return {}


def get_target_path(movie, scene):
    site_pathname = scene.get('site', {}).get('name', '_unsorted')
    new_site_path = path.join(TARGET_DIRECTORY_PATH, site_pathname)

    new_filename = "{title} [{shootid}]{f.extension}".format(title=scene.get('title'),
                                                              shootid=scene.get('shootid'),
                                                              f=movie.file_properties)
    return path.join(new_site_path, new_filename)


class Movie(models.Model):
    api = models.CharField(max_length=50, null=True)
    file_properties = models.OneToOneField(FileProperties, related_name='file_properties')
    sorted_properties = models.OneToOneField(FileProperties, related_name='sorted_properties', null=True)
    # scene_properties contains an id to find the properties again with the specified API
    scene_properties = models.IntegerField(default=0)

    def serialize(self):
        status = 'okay'

        scene = get_scene_from_movie(self)
        if not scene:
            status = 'unrecognized'

        #in_target = self.targetporndirectory_set.exists()
        in_target = TargetPornDirectory.objects.get().movies.filter(scene_properties=self.scene_properties).exists()
        if status == 'okay' and in_target:
            status = 'duplicate'

        target_path = get_target_path(self, scene)
        if not self.sorted_properties or not path.exists(target_path):
            sorted_state = 'missing'
        else:
            if path.islink(target_path):
                sorted_state = 'link'
            else:
                sorted_state = 'exists'

        if self.porndirectory_set.exists():
            porn_directory = self.porndirectory_set.get()
        else:
            porn_directory = self.targetporndirectory_set.get()
        return {
                'directory_name': porn_directory.name,
                'directory_id': porn_directory.id,
                'type': 'movie',
                'movie_id': self.id,
                'api': '' if DEBUG_SFW else self.api,
                'full_path': self.file_properties.full_path,
                'target_path': target_path,
                'sorted_state': sorted_state,
                'title': '' if DEBUG_SFW else (scene.get('title') if 'title' in scene else self.file_properties.file_name),
                'scene_site': '' if DEBUG_SFW else scene.get('site', {}).get('name'),
                'scene_date': scene.get('date'),
                'scene_id': scene.get('shootid'),
                'status': status,
                'in_target': in_target
        }

    def get_video_path(self):
        return '{}{}/{}/{}'.format(STATIC_URL, DIRECTORY_STATIC_LINK_NAME,
                                   self.porndirectory_set.get().id, self.file_properties.relative_path)


class TargetPornDirectory(models.Model):
    name = models.CharField(max_length=100, default='Target')
    is_read_only = models.BooleanField(default=False)
                                                    #manage.py,src, .kinksorter
    path = models.CharField(default=path.realpath(path.join(BASE_DIR, '..', '..')), max_length=500)
    date_added = models.DateTimeField(default=datetime.datetime.now)
    movies = models.ManyToManyField(Movie)

    def serialize(self):
        return {
            'porn_directory_path': path.realpath(self.path),
            'porn_directory_date': self.date_added,
            'porn_directory_id': 0,
            'porn_directory_movies_count': self.movies.count(),
            'is_target': True
        }


class PornDirectory(models.Model):
    name = models.CharField(max_length=100, default='<PornDirectory>')
    path = models.CharField(max_length=500)
    date_added = models.DateTimeField(default=datetime.datetime.now)
    movies = models.ManyToManyField(Movie)
    is_read_only = models.BooleanField(default=True)

    def serialize(self):
        return {
            'porn_directory_name': self.name,
            'porn_directory_path': path.realpath(self.path),
            'porn_directory_date': self.date_added,
            'porn_directory_id': self.id,
            'porn_directory_read_only': self.is_read_only,
            'porn_directory_movies_count': self.movies.count(),
            'is_target': False
        }


class CurrentTask(models.Model):
    name = models.CharField(max_length=200)
    started = models.DateTimeField(default=django.utils.timezone.now)
    ended = models.BooleanField(default=False)
    progress_max = models.IntegerField(default=0)
    progress_current = models.IntegerField(default=0)


