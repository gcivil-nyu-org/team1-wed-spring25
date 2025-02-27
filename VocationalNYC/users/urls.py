from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("", include("allauth.urls")),
    path("profile/", TemplateView.as_view(template_name="profile.html"), name="profile"),
]