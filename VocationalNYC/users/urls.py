from django.urls import path, include
from django.views.generic import TemplateView
from allauth.account.views import SignupView
from .forms import StudentSignupForm, ProviderSignupForm
from . import views

urlpatterns = [
    path(
        "signup/",
        SignupView.as_view(form_class=StudentSignupForm),
        name="account_signup",
    ),
    # PROVIDER SIGNUP
    path(
        "signup/provider/",
        SignupView.as_view(form_class=ProviderSignupForm),
        name="account_signup_provider",
    ),
    path("", include("allauth.urls")),
    path("profile/", TemplateView.as_view(template_name="profile.html"), name="profile"),
    path('provider/<int:pk>/', views.ProviderDetailView.as_view(), name='provider_detail'),
    path('provider/', views.ProviderListView.as_view(), name='provider_list'),
]