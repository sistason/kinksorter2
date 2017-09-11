from django.conf.urls import url

from kinksorter_app.functionality import io_handling_directory, io_handling_movie, sorting
from kinksorter_app import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^play_video/(?P<movie_id>\d+)/?$', views.play_video),
    url(r'^sort/?$', sorting.sort_into_target),
    url(r'^get_current_task/?$', sorting.get_current_task_request),
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
    url(r'^movie/recognize/?$', io_handling_movie.recognize_movie_request),
    url(r'^movie/recognize_multiple/?$',
        io_handling_movie.recognize_multiple_movies_request),
    url(r'^movie/delete/?$', io_handling_movie.delete_movie_request),
    url(r'^movie/remove_from_main/?$', io_handling_movie.remove_movie_from_target_request),
    url(r'^movie/merge/?$', io_handling_movie.merge_movie_request),
    url(r'^movie/merge_multiple/?$', io_handling_movie.merge_multiple_movies_request),
    url(r'^movie/get/?$', io_handling_movie.get_movie_request),
]

