from django.conf.urls import url

import kinksorter_app.functionality.io_handling_movie
from kinksorter_app.functionality import io_handling_directory, io_handling_movie
from kinksorter_app import views

urlpatterns = [
    url(r'^$', views.index),
]

urlpatterns += [
    url(r'^porn_directory/add/?$', io_handling_directory.add_new_porn_directory_request),
    url(r'^porn_directory/delete/?$', io_handling_directory.delete_porn_directory_request),
    url(r'^porn_directory/update/?$', io_handling_directory.update_porn_directory_request),
    url(r'^porn_directory/reset/?$', io_handling_directory.reset_porn_directory_request),
    url(r'^porn_directory/rerecognize/?$', io_handling_directory.rerecognize_porn_directory_request),
    url(r'^porn_directory/change_name/?$', io_handling_directory.change_porn_directory_name_request),
    url(r'^porn_directory/get_porn_directory/?$', io_handling_directory.get_porn_directory_request),
    url(r'^porn_directory/get_porn_directory_ids/?$', io_handling_directory.get_porn_directory_ids_request),
]

urlpatterns += [
    url(r'^movie/recognize/?$', kinksorter_app.functionality.io_handling_movie.recognize_movie_request),
    url(r'^movie/recognize_multiple/?$',
        kinksorter_app.functionality.io_handling_movie.recognize_multiple_movies_request),
    url(r'^movie/delete/?$', kinksorter_app.functionality.io_handling_movie.delete_movie_request),
    url(r'^movie/remove_from_main/?$', io_handling_movie.remove_movie_from_target_request),
    url(r'^movie/merge/?$', kinksorter_app.functionality.io_handling_movie.merge_movie_request),
    url(r'^movie/merge_multiple/?$', kinksorter_app.functionality.io_handling_movie.merge_multiple_movies_request),
    url(r'^movie/get/?$', kinksorter_app.functionality.io_handling_movie.get_movie_request),
]