from django.db import models
import datetime
from os import path
import logging

from kinksorter.settings import BASE_DIR, DEBUG_SFW
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

        if status == 'okay' and self.mainstorage_set.exists():
            status = 'in_main'

        new_storage = self.storage_set.get()
        return {
                'storage_name': new_storage.name,
                'storage_id': new_storage.id,
                'movie_id': self.id,
                'api': '' if DEBUG_SFW else self.api,
                'full_path': self.file_properties.full_path,
                'watch_scene': 'file://{}'.format(self.file_properties.full_path),
                'title': '' if DEBUG_SFW else (scene.get('title') if 'title' in scene else self.file_properties.file_name),
                'scene_site': '' if DEBUG_SFW else scene.get('site', {}).get('name'),
                'scene_date': scene.get('date'),
                'scene_id': scene.get('shootid'),
                'status': status
        }


class Storage(models.Model):
    path = models.CharField(max_length=500)
    name = models.CharField(max_length=100, default='<Storage>', null=True)
    read_only = models.BooleanField(default=True)
    date_added = models.DateTimeField(default=datetime.datetime.now)
    movies = models.ManyToManyField(Movie)


class MainStorage(models.Model):
                                                    #manage.py,src, .kinksorter
    path = models.CharField(default=path.join(BASE_DIR, '..', '..', '..'), max_length=500)
    date_added = models.DateTimeField(default=datetime.datetime.now)
    movies = models.ManyToManyField(Movie)