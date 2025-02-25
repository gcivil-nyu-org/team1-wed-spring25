from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path("", include("allauth.urls")),
    path("profile/", TemplateView.as_view(template_name="profile.html"), name="profile"),
    path('provider/<int:pk>/', views.ProviderDetailView.as_view(), name='provider_detail'),
    path('provider/', views.ProviderListView.as_view(), name='provider_list'),
]