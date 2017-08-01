
from django.http.response import HttpResponse, JsonResponse

from kinksorter_app.functionality.storage_handling import StorageHandler, change_storage_name, \
    get_storage, get_storage_ids, get_storage_data
from kinksorter_app.functionality.movie_handling import RecognitionHandler, delete_movie, add_movie_to_main


def add_new_storage_request(request):
    storage_path = request.GET.get('storage_path')
    if storage_path:
        name = request.GET.get('name')
        read_only = True if request.GET.get('read_only') else False
        stor_ = StorageHandler(storage_path, name=name, read_only=read_only)
        if stor_:
            stor_.scan()
            return HttpResponse('Storage created', status=200)
        return HttpResponse('Storage already exists', status=406)
    return HttpResponse('No storage_path in request', status=400)


def update_storage_request(request):
    storage_id = request.GET.get('storage_id')
    if storage_id and storage_id.isdigit():
        stor_ = StorageHandler(int(storage_id))
        if stor_:
            stor_.scan()
            return HttpResponse('Storage updating', status=200)
        return HttpResponse('Storage does not exist', status=406)
    return HttpResponse('Storage-ID malformed', status=400)


def change_storage_name_request(request):
    storage_id = request.GET.get('storage_id')
    new_storage_name = request.GET.get('new_storage_name')
    if storage_id and storage_id.isdigit() and new_storage_name:
        if change_storage_name(int(storage_id), new_storage_name):
            return HttpResponse('Storage name changed', status=200)
        return HttpResponse('Storage does not exist', status=406)

    return HttpResponse('Storage-ID malformed', status=400)


def delete_storage_request(request):
    storage_id = request.GET.get('storage_id')
    if storage_id and storage_id.isdigit():
        stor_ = StorageHandler(int(storage_id))
        if stor_:
            stor_.delete()
            return HttpResponse('Storage deleted', status=200)
        return HttpResponse('Storage does not exist', status=406)
    return HttpResponse('Storage-ID malformed', status=400)


def recognize_movie_request(request):
    movie_id = request.GET.get('movie_id')

    recognition_handler = RecognitionHandler(movie_id)
    if recognition_handler.movie is None:
        return HttpResponse('No Movie with that id found', status=400)

    new_name = request.GET.get('new_scene_name')
    new_sid = request.GET.get('new_scene_id')
    if not new_sid.isdigit():
        return HttpResponse('SceneID has to be an integer', status=400)

    if recognition_handler.recognize(new_name=new_name, new_sid=int(new_sid)):
        return HttpResponse('Movie recognized', status=200)
    else:
        return HttpResponse('Movie could not be recognized', status=406)


def delete_movie_request(request):
    movie_id = request.GET.get('movie_id')
    if not movie_id or not movie_id.isdigit():
        return HttpResponse('No Movie with that id found', status=400)
    delete_movie(int(movie_id))
    return HttpResponse('Movie deleted', status=200)


def add_movie_to_main_request(request):
    movie_id = request.GET.get('movie_id')
    if not movie_id or not movie_id.isdigit():
        return HttpResponse('MovieID has to be an integer', status=400)
    if not add_movie_to_main(int(movie_id)):
        return HttpResponse('No Movie with that id found', status=404)
    return HttpResponse('Movie added', status=200)


def get_storage_request(request):
    storage_id = request.GET.get('storage_id')
    if storage_id and storage_id.isdigit():
        data = get_storage_data(storage_id=storage_id)
        if data is None:
            return HttpResponse('No storage with that id found', status=404)

        return JsonResponse(data, safe=False)

    return HttpResponse('Storage-ID malformed', status=400)


def get_storage_ids_request(request):
    return JsonResponse(get_storage_ids(), safe=False)
