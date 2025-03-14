from django.urls import path
from . import views

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course_list"),
    path("<int:pk>/", views.CourseDetailView.as_view(), name="course_detail"),
    path("search_result/", views.search_result, name="search_result"),
    # path('api/course_data/', views.course_data, name='course_data'),
    # path('map/', views.map_view, name='map_view'),
]
