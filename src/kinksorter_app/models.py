from django.db import models
import datetime
from os import path

from kinksorter.settings import BASE_DIR


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