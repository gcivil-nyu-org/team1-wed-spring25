from django.urls import path, include

# from django.views.generic import TemplateView
# from allauth.account.views import SignupView

# from .forms import StudentSignupForm, ProviderSignupForm
from .views import CustomSignupView, provider_verification_view, check_provider_name
from . import views

urlpatterns = [
    path("signup/", CustomSignupView.as_view(), name="account_signup"),
    path(
        "provider_verification/",
        provider_verification_view,
        name="provider_verification",
    ),
    path("profile/", views.profile_view, name="profile"),
    path("", include("allauth.urls")),
    path(
        "provider/<int:pk>/", views.ProviderDetailView.as_view(), name="provider_detail"
    ),
    path("provider/", views.ProviderListView.as_view(), name="provider_list"),
    path('check_provider_name/', check_provider_name, name='check_provider_name'),
]
