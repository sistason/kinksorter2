from django.shortcuts import render
from django.http.response import HttpResponse
from kinksorter_app.functionality.movie_handling import get_movie


def index(request):
    return render(request, 'index.html')


def play_video(request, movie_id):
    movie = get_movie(movie_id)
    # TODO: transcode everything != mp4 to mp4 for html5-video
    # TODO: pseudo-streaming = seek farther than buffer. preload=none does not work
    video = """<!DOCTYPE html><head><title></title></head><body>
<video name='{}' controls autoplay preload='none' width='70%'>
    <source src="{}" type="video/mp4"></source>
</video></body>""".format(movie.file_properties.file_name, movie.get_video_path())
    return HttpResponse(video, status=200)
