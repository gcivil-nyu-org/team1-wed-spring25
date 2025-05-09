from django.urls import path
from . import views

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course_list"),
    path("<int:pk>/", views.CourseDetailView.as_view(), name="course_detail"),
    path("search_result/", views.search_result, name="search_result"),
    path("course_map/", views.course_map, name="course_map"),
    path("sort/", views.sort_by, name="course_sort"),
    path("manage_courses/", views.manage_courses, name="manage_courses"),
    path("new_course/", views.post_new_course, name="new_course"),
    path("delete_course/<int:course_id>/", views.delete_course, name="delete_course"),
    path("edit_course/<int:course_id>/", views.edit_course, name="edit_course"),
    path("course_comparison/", views.course_comparison, name="course_comparison"),
    path("add_to_comparison/", views.add_to_comparison, name="add_to_comparison"),
    path(
        "remove_from_comparison/",
        views.remove_from_comparison,
        name="remove_from_comparison",
    ),
    path("clear_comparison/", views.clear_comparison, name="clear_comparison"),
]
