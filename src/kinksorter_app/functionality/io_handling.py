
from django.http.response import HttpResponse, JsonResponse

from kinksorter_app.functionality.storage_handling import StorageHandler, \
    get_storage, get_storage_ids, get_storage_data
from kinksorter_app.functionality.movie_handling import RecognitionHandler, delete_movie, merge_movie, get_movie, \
    remove_movie_from_main


def add_new_storage_request(request):
    storage_path = request.GET.get('storage_path')
    if storage_path:
        name = request.GET.get('name')
        read_only = True if request.GET.get('read_only') else False
        stor_ = StorageHandler(storage_path, name=name, read_only=read_only)
        if stor_:
            stor_.scan()
            return JsonResponse(get_storage_data(storage=stor_.storage), safe=False)
        return HttpResponse('Storage already exists', status=406)
    return HttpResponse('No storage_path in request', status=400)


def update_storage_request(request):
    storage_handler = get_storage_by_id(request)
    if type(storage_handler) == HttpResponse:
        return storage_handler

    storage_handler.scan()
    return HttpResponse('Storage updating', status=200)


def reset_storage_request(request):
    storage_handler = get_storage_by_id(request)
    if type(storage_handler) == HttpResponse:
        return storage_handler

    if storage_handler.reset():
        return HttpResponse('Storage resetting', status=200)
    return HttpResponse('Error resetting storage', status=500)


def rerecognize_storage_request(request):
    storage_handler = get_storage_by_id(request)
    if type(storage_handler) == HttpResponse:
        return storage_handler

    unrecognized_movies = storage_handler.rerecognize()
    if unrecognized_movies:
        return JsonResponse(unrecognized_movies, safe=False)
    return HttpResponse('Error rerecognizing storage', status=500)


def change_storage_name_request(request):
    storage_handler = get_storage_by_id(request)
    if type(storage_handler) == HttpResponse:
        return storage_handler

    new_storage_name = request.GET.get('new_storage_name')
    if new_storage_name:
        if storage_handler.change_name(new_storage_name):
            return HttpResponse('Storage name changed', status=200)


def get_storage_by_id(request):
    storage_id = request.GET.get('storage_id')
    if storage_id and storage_id.isdigit():
        stor_ = StorageHandler(int(storage_id))
        if stor_:
            return stor_
        return HttpResponse('Storage does not exist', status=406)
    return HttpResponse('Storage-ID malformed', status=400)


def delete_storage_request(request):
    storage_handler = get_storage_by_id(request)
    if type(storage_handler) == HttpResponse:
        return storage_handler

    storage_handler.delete()
    return HttpResponse('Storage deleted', status=200)


def get_storage_request(request):
    storage_handler = get_storage_by_id(request)
    if type(storage_handler) == HttpResponse:
        return storage_handler

    data = get_storage_data(storage=storage_handler.storage)
    return JsonResponse(data, safe=False)


def recognize_movie_request(request):
    movie_id = request.GET.get('movie_id')

    recognition_handler = RecognitionHandler(movie_id)
    if recognition_handler.movie is None:
        return HttpResponse('No Movie with that id found', status=404)

    new_name = request.GET.get('new_scene_name')
    new_sid = request.GET.get('new_scene_id')
    if not new_sid.isdigit():
        return HttpResponse('SceneID has to be an integer', status=400)

    recognized_movie = recognition_handler.recognize(new_name=new_name, new_sid=int(new_sid))
    if recognized_movie is not None:
        return JsonResponse(recognized_movie.serialize(), safe=False)

    return HttpResponse('Movie could not be recognized', status=406)


def recognize_multiple_movies_request(request):
    movie_ids = request.GET.getlist('movie_ids[]')
    if [m for m in movie_ids if not m.isdigit()]:
        return HttpResponse('MovieIDs has to be a list of integers', status=400)

    recognized = []
    for movie_id in movie_ids:
        recognition_handler = RecognitionHandler(movie_id)
        if recognition_handler.movie is None:
            continue
        recognized_movie = recognition_handler.recognize()
        if recognized_movie is not None:
            recognized.append(recognized_movie.serialize())

    return JsonResponse(recognized, safe=False)


def delete_movie_request(request):
    movie_id = request.GET.get('movie_id')
    if not movie_id or not movie_id.isdigit():
        return HttpResponse('No Movie with that id found', status=400)
    delete_movie(int(movie_id))
    return HttpResponse('Movie deleted', status=200)


def remove_movie_from_main_request(request):
    movie_id = request.GET.get('movie_id')
    if not movie_id or not movie_id.isdigit():
        return HttpResponse('No Movie with that id found', status=400)
    remove_movie_from_main(movie_id)
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


def get_storage_ids_request(request):
    return JsonResponse(get_storage_ids(), safe=False)


def get_movie_request(request):
    movie_id = request.GET.get('movie_id')
    if not movie_id or not movie_id.isdigit():
        return HttpResponse('MovieID has to be an integer', status=400)

    movie = get_movie(movie_id)
    if movie is None:
        return HttpResponse('No Movie with that id found', status=404)

    return JsonResponse(movie.serialize(), safe=False)