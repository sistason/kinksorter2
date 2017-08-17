from django.conf.urls import url

from kinksorter_app.functionality import io_handling
from kinksorter_app import views

urlpatterns = [
    url(r'^$', views.index),
]

urlpatterns += [
    url(r'^storage/add/?$', io_handling.add_new_storage_request),
    url(r'^storage/delete/?$', io_handling.delete_storage_request),
    url(r'^storage/update/?$', io_handling.update_storage_request),
    url(r'^storage/reset/?$', io_handling.reset_storage_request),
    url(r'^storage/change_name/?$', io_handling.change_storage_name_request),
    url(r'^storage/get_storage/?$', io_handling.get_storage_request),
    url(r'^storage/get_storage_ids/?$', io_handling.get_storage_ids_request),
]

urlpatterns += [
    url(r'^movie/recognize/?$', io_handling.recognize_movie_request),
    url(r'^movie/delete/?$', io_handling.delete_movie_request),
    url(r'^movie/remove_from_main/?$', io_handling.remove_movie_from_main_request),
    url(r'^movie/merge/?$', io_handling.merge_movie_request),
    url(r'^movie/get/?$', io_handling.get_movie_request),
]