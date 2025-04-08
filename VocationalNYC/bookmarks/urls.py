# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("bookmark_list/", views.BookmarkListView.as_view(), name="bookmark_list"),
    path(
        "bookmark_list/<int:list_id>/",
        views.BookmarkListDetailView.as_view(),
        name="bookmark_list_detail",
    ),
    path(
        "bookmark_list/<int:list_id>/delete_bookmark/<int:bookmark_id>/",
        views.delete_bookmark,
        name="delete_bookmark",
    ),
    path(
        "bookmark_list/create/", views.create_bookmark_list, name="create_bookmark_list"
    ),
    path(
        "bookmark_list/<int:list_id>/delete/",
        views.delete_bookmark_list,
        name="delete_bookmark_list",
    ),
    path(
        "courses/<int:course_id>/add_bookmark/", views.add_bookmark, name="add_bookmark"
    ),
    path('bookmark_list/<int:list_id>/rename/', views.rename_bookmark_list, name='rename_bookmark_list'),
]
