# users/middleware.py
from django.shortcuts import redirect
from django.urls import reverse


class TrainingProviderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user

        if (
            user.is_authenticated
            and not user.is_active
            and getattr(user, "role", None) == "training_provider"
        ):

            # if request.path.startswith('/accounts/provider_verification/'):
            #     return None
            # else:
            #     return redirect('provider_verification')
            provider_verification_url = reverse("provider_verification")
            if request.path != provider_verification_url:
                return redirect(provider_verification_url)

        return None
