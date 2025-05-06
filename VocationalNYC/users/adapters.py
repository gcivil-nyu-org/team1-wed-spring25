import logging
from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

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
        if getattr(user, "role", "") == "training_provider":
            if user.is_active:
                logger.debug(
                    f"Active training_provider {user.username} redirected to profile."
                )
                return reverse("manage_courses")
            else:
                logger.debug(
                    f"Inactive training_provider {user.username} redirected to provider_verification."
                )
                return reverse("provider_verification")
        return reverse("home")

    def respond_inactive(self, request, user):
        if getattr(user, "role", None) == "training_provider":
            logger.debug(
                f"Redirecting training_provider user {user.username} to provider_verification"
            )
            return reverse("provider_verification")
        return None
