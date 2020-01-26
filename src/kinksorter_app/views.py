from django.shortcuts import render
from django.http.response import HttpResponse
from kinksorter_app.functionality.movie_handling import get_movie


def index(request):
    return render(request, 'management.html')


def play_video(request, movie_id):
    movie = get_movie(movie_id)
    data = {'name': movie.file_name, 'path': movie.get_video_path()}
    return render(request, 'video.html', context=data)
