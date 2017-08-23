from django.db import models
import datetime
from os import path
import logging

from kinksorter.settings import BASE_DIR, DEBUG_SFW, DIRECTORY_STATIC_LINK_NAME, STATIC_URL
from kinksorter_app.apis.api_router import APIS


class FileProperties(models.Model):
    full_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=200)
    file_size = models.IntegerField()
    extension = models.CharField(max_length=10)
    relative_path = models.CharField(max_length=300)


class Movie(models.Model):
    file_properties = models.ForeignKey(FileProperties)
    api = models.CharField(max_length=50, null=True)
    # scene_properties contains an id to find the properties again with the specified API
    scene_properties = models.IntegerField(default=0)

    def serialize(self):
        status = 'okay'
        scene = {}

        if not self.scene_properties:
            status = 'unrecognized'
        else:
            api = APIS.get(self.api, APIS.get('default'))
            if api:
                scene = api.query('shoot', 'shootid', self.scene_properties)
                if len(scene) > 1:
                    logging.warning('Multiple scenes for shootid {} found! ({})'.format(self.scene_properties, scene))
                scene = scene[0]

        if status == 'okay' and self.targetporndirectory_set.exists():
            status = 'in_target'

        porn_directory = self.porndirectory_set.get()
        return {
                'directory_name': porn_directory.name,
                'directory_id': porn_directory.id,
                'type': 'movie',
                'movie_id': self.id,
                'api': '' if DEBUG_SFW else self.api,
                'full_path': self.file_properties.full_path,
                'title': '' if DEBUG_SFW else (scene.get('title') if 'title' in scene else self.file_properties.file_name),
                'scene_site': '' if DEBUG_SFW else scene.get('site', {}).get('name'),
                'scene_date': scene.get('date'),
                'scene_id': scene.get('shootid'),
                'status': status
        }

    def get_video_path(self):
        return '{}{}/{}/{}'.format(STATIC_URL, DIRECTORY_STATIC_LINK_NAME,
                                   self.porndirectory_set.get().id, self.file_properties.relative_path)


class TargetPornDirectory(models.Model):
                                                    #manage.py,src, .kinksorter
    path = models.CharField(default=path.join(BASE_DIR, '..', '..', '..'), max_length=500)
    date_added = models.DateTimeField(default=datetime.datetime.now)
    movies = models.ManyToManyField(Movie)

    def serialize(self):
        return {
            'porn_directory_path': self.path,
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
            'porn_directory_path': self.path,
            'porn_directory_date': self.date_added,
            'porn_directory_id': self.id,
            'porn_directory_read_only': self.is_read_only,
            'porn_directory_movies_count': self.movies.count(),
            'is_target': False
        }
