from django.db import models

# Create your models here.


class Storage(models.Model):
    path = models.CharField(max_length=500)
    name = models.CharField(max_length=100, default='<Storage>')
    date_added = models.DateTimeField()
    movies = models.ManyToManyField(Movie)
    plugin = models.CharField(max_length=50)


class Movie(models.Model):
    file_properties = models.ForeignKey(FileProperties)


class KinkComMovie(Movie):
    scene_properties = models.ForeignKey(KinkComSceneProperties)


class SceneProperties(models.Model):
    name = models.CharField(max_length=500)
    date = models.DateField()
    performers = models.ManyToManyField(models.CharField)


class KinkComSceneProperties(SceneProperties):
    site = models.CharField(max_length=100)
    shootid = models.IntegerField()


class FileProperties(models.Model):
    file_name = models.CharField(max_length=200)
    extension = models.CharField(max_length=10)
    relative_path = models.CharField(max_length=300)
