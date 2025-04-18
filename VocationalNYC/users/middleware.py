# users/middleware.py
from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404
from django.http import HttpResponseRedirect


class AdminRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            hasattr(request, "user")
            and request.user.is_authenticated
            and (
                request.user.role == "administrator"
                or request.user.is_superuser
                or request.user.is_staff
            )
        ):
            # Allow access to media files
            if not (
                request.path.startswith("/media/") or request.path.startswith("/admin/")
            ):
                return HttpResponseRedirect("/admin/")
        return self.get_response(request)


class TrainingProviderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user

        try:
            url_name = resolve(request.path_info).url_name
            if url_name == "check_provider_name" or url_name == "account_logout":
                return None
        except Resolver404:
            pass

        if (
            user.is_authenticated
            and not user.is_active
            and getattr(user, "role", None) == "training_provider"
        ):
            provider_verification_url = reverse("provider_verification")
            if request.path != provider_verification_url:
                return redirect(provider_verification_url)

        return None
