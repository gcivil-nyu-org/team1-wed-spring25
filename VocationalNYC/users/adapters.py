import logging
from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from django.http import HttpResponseRedirect

logger = logging.getLogger(__name__)


class MyAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return True

    def is_open_for_login(self, request, user):
        if getattr(user, "role", None) == "training_provider":
            logger.debug(
                f"Training provider {user.username} allowed for login regardless of is_active."
            )
            return True
        return user.is_active  # Base implementation for non-training providers

    def get_login_redirect_url(self, request):
        user = request.user
        if user.is_superuser or user.is_staff:
            return "/admin/"
        if getattr(user, "role", "") == "training_provider" and not user.is_active:
            logger.debug(
                f"Redirecting training_provider {user.username} to provider_verification."
            )
            return HttpResponseRedirect(reverse("provider_verification"))
        return reverse("profile")

    def respond_inactive(self, request, user):
        if getattr(user, "role", None) == "training_provider":
            logger.debug(
                f"Redirecting training_provider user {user.username} to provider_verification"
            )
            return reverse("provider_verification")
        return None
