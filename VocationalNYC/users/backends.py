from django.contrib.auth.backends import ModelBackend


class TrainingProviderVerificationBackend(ModelBackend):
    def user_can_authenticate(self, user):
        # Allow inactive users to authenticate if they are training providers
        if not user.is_active and getattr(user, "role", None) == "training_provider":
            return True
        return super().user_can_authenticate(user)

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(
            request, username=username, password=password, **kwargs
        )
        if user and not user.is_active and user.role == "training_provider":
            setattr(user, "_verified_inactive_provider", True)
        return user
