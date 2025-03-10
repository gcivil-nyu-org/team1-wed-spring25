from django.urls import path
from . import views
from .views import CourseListView, CourseDetailView

urlpatterns = [
<<<<<<< HEAD
    path('', views.CourseListView.as_view(), name='course_list'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('search_result/', views.search_result, name='search_result'),
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
]
=======
    path("", views.CourseListView.as_view(), name="course_list"),
    path("<int:pk>/", views.CourseDetailView.as_view(), name="course_detail"),
    path("search_result/", views.search_result, name="search_result"),
]
>>>>>>> develop
