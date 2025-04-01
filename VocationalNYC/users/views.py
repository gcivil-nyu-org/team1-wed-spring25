import requests

# import os
# from django.conf import settings
# from django.core.files.storage import default_storage
from django.shortcuts import render, redirect
from django.views import generic
from allauth.account.views import SignupView
from .forms import CustomSignupForm, ProviderVerificationForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.db import IntegrityError, transaction

from users.models import Provider, Student
from bookmarks.models import BookmarkList


def login(request):
    return render(request, "users/login.html")


class CustomSignupView(SignupView):
    form_class = CustomSignupForm
    template_name = "account/signup.html"

    def form_valid(self, form):
        # 1. Create the user via the form
        user = form.save(self.request)

        # 2. Create default bookmark list for the new user
        try:
            with transaction.atomic():
                BookmarkList.objects.create(user=user, name="default")
                messages.success(
                    self.request, "Deafault Bookmark list created successfully."
                )
        except IntegrityError:
            messages.error(self.request, "Failed to create default bookmark.")

        # 3. Log the user in
        auth_login(
            self.request,
            user,
            backend="allauth.account.auth_backends.AuthenticationBackend",
        )

        # Redirect based on role:
        if user.role == "training_provider":
            return redirect("provider_verification")
        else:
            return redirect("profile")


@login_required
def profile_view(request):
    if request.method == "POST":
        if 'provider_form' in request.POST and request.user.role == "training_provider":
            provider_form = ProviderVerificationForm(request.POST, request.FILES, instance=getattr(request.user, 'provider_profile', None))
            form = ProfileUpdateForm(instance=request.user)
            if provider_form.is_valid():
                provider = provider_form.save(commit=False)
                provider.user = request.user
                provider.save()
                return redirect("profile")
        else:
            form = ProfileUpdateForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect("profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {"user": request.user, "role": request.user.role, "form": form}

    if request.user.role == "training_provider":
        try:
            provider = Provider.objects.get(user=request.user)
            context["provider"] = provider
            context["provider_verification_form"] = ProviderVerificationForm(instance=provider)
        except Provider.DoesNotExist:
            context["provider_verification_form"] = ProviderVerificationForm()
    elif request.user.role == "career_changer":
        try:
            student = request.user.student_profile
            context["student"] = student
            # Add bookmark lists to context
            bookmark_lists = request.user.bookmark_list.all().prefetch_related('bookmark__course')
            context["bookmark_lists"] = bookmark_lists
            # Add reviews to context
            reviews = request.user.reviews.select_related('course').order_by('-created_at')
            context["reviews"] = reviews
        except Student.DoesNotExist:
            pass

    return render(request, "users/profile.html", context)


@login_required
def provider_verification_view(request):
    if request.user.role != "training_provider":
        return redirect("profile")

    if request.method == "POST":
        form = ProviderVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.user = request.user
            provider.verification_status = False
            provider.save()
            return render(
                request,
                "account/provider_verification_success.html",
                {"provider": provider}
            )
    else:
        form = ProviderVerificationForm()
    
    return render(request, "account/provider_verification.html", {"form": form})


class ProviderDetailView(generic.DetailView):
    model = Provider
    template_name = "profile/provider_detail.html"
    context_object_name = "provider"


class ProviderListView(generic.ListView):
    model = Provider
    template_name = "profile/provider_list.html"
    context_object_name = "all_provider"

    def get_queryset(self):
        API_URL = "https://data.cityofnewyork.us/resource/fgq8-am2v.json"
        response = requests.get(API_URL)
        if response.status_code == 200:
            all_data = response.json()

            for data in all_data:
                provider_name = data.get("organization_name", "").strip()

                if not provider_name:
                    continue  # skip invalid data

                # check whether provider exists
                provider, created = Provider.objects.get_or_create(
                    name=provider_name,
                    defaults={
                        "phone_num": data.get("phone1", "0000000000"),
                        "address": data.get("address1", "Unknown"),
                        "open_time": data.get("open_time", "N/A"),
                        "provider_desc": data.get(
                            "provider_description", "No description"
                        ),
                        "website": data.get("website", ""),
                    },
                )

        else:
            print(f"Call API failed, the status code is: {response.status_code}")

        return Provider.objects.all()
