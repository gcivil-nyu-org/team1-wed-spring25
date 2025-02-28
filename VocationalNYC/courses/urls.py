from django.urls import path, include
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('courses/', views.CourseListView.as_view(), name='course_list'),
]
