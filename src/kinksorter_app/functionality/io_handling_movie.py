from django.http import HttpResponse, JsonResponse

from kinksorter_app.functionality.movie_handling import get_movie, recognize_movie, recognize_multiple, delete_movie, \
    remove_movie_from_target, merge_movie
from kinksorter_app.functionality.directory_handling import get_target_porn_directory
from kinksorter_app.models import CurrentTask


def recognize_movie_request(request):
    movie_id = request.GET.get('movie_id')

    movie = get_movie(movie_id)
    if movie is None:
        return HttpResponse('No Movie with that id found', status=404)

    new_name = request.GET.get('new_scene_name')
    new_sid = request.GET.get('new_scene_id')
    if not new_sid.isdigit():
        return HttpResponse('SceneID has to be an integer', status=400)

    recognized_movie = recognize_movie(movie, None, new_name=new_name, new_sid=int(new_sid))
    if recognized_movie is not None:
        return JsonResponse(recognized_movie.serialize(), safe=False)

    return HttpResponse('Movie could not be recognized', status=406)


def recognize_multiple_movies_request(request):
    movie_ids = request.GET.getlist('movie_ids[]')
    if [m for m in movie_ids if not m.isdigit()]:
        return HttpResponse('MovieIDs has to be a list of integers', status=400)

    if CurrentTask.objects.filter(name__ne='Recognizing').exists():
        return HttpResponse('Task running! Wait for completion!.', status=503)

    recognized = recognize_multiple(movie_ids, None)
    return JsonResponse(recognized, safe=False)


def delete_movie_request(request):
    movie_id = request.GET.get('movie_id')
    if not movie_id or not movie_id.isdigit():
        return HttpResponse('No Movie with that id found', status=400)
    delete_movie(int(movie_id))
    return HttpResponse('Movie deleted', status=200)


def remove_movie_from_target_request(request):
    movie_id = request.GET.get('movie_id')
    if not movie_id or not movie_id.isdigit():
        return HttpResponse('No Movie with that id found', status=400)
    remove_movie_from_target(movie_id)
    return HttpResponse('Movie removed', status=200)


def merge_movie_request(request):
    movie_id = request.GET.get('movie_id')
    if not movie_id or not movie_id.isdigit():
        return HttpResponse('MovieID has to be an integer', status=400)

    movie = merge_movie(movie_id)
    if movie is None:
        return HttpResponse('No Movie with that id found', status=404)

    return JsonResponse(movie.serialize(), safe=False)


def merge_multiple_movies_request(request):
    movie_ids = request.GET.getlist('movie_ids[]')
    if [m for m in movie_ids if not m.isdigit()]:
        return HttpResponse('MovieIDs has to be a list of integers', status=400)

    return JsonResponse([merge_movie(movie_id).id for movie_id in movie_ids], safe=False)


def get_movie_request(request):
    movie_id = request.GET.get('movie_id')
    if not movie_id or not movie_id.isdigit():
        return HttpResponse('MovieID has to be an integer', status=400)

    movie = get_movie(movie_id)
    if movie is None:
        return HttpResponse('No Movie with that id found', status=404)

    return JsonResponse(movie.serialize(), safe=False)