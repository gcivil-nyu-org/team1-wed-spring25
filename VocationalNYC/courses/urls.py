from django.urls import path
from . import views
from .views import course_map, course_data

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course_list"),
    path("<int:pk>/", views.CourseDetailView.as_view(), name="course_detail"),
    path("search_result/", views.search_result, name="search_result"),
    path("map/", course_map, name="course_map"),
    path("api/course_data/", course_data, name="course_data"),
    path("sort/", views.sort_by, name="course_sort"),
    path("new_course/", views.post_new_course, name="new_course"),
    # path('course/delete/<int:course_id>/', views.delete_course, name='delete_course'),
]
