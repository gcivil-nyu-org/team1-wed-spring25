import requests
import logging
import os

from django.shortcuts import render, redirect
from django.views import generic
from allauth.account.views import SignupView, LoginView
from .forms import (
    CustomSignupForm,
    ProviderVerificationForm,
    ProfileUpdateForm,
    ProviderUpdateForm,
    StudentProfileForm,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.db import transaction

# from allauth.account.views import LoginView
from django.views.decorators.http import require_POST
import json

from users.models import Provider, Student, Tag
from bookmarks.models import BookmarkList
from review.models import Review

from allauth.account.views import PasswordResetView
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse

logger = logging.getLogger(__name__)


def login(request):
    return render(request, "users/login.html")


class CustomLoginView(LoginView):
    def form_valid(self, form):
        user = form.user
        auth_login(self.request, user)

        # Always redirect admin to admin dashboard
        if getattr(user, "role", "") == "administrator":
            return HttpResponseRedirect("/admin/")

        if getattr(user, "role", "") == "training_provider":
            if not user.is_active:
                print(f"Redirecting inactive provider {user.username} to verification")
                return HttpResponseRedirect(reverse("provider_verification"))
            else:
                print(f"Redirecting active provider {user.username} to manage courses")
                return HttpResponseRedirect(reverse("manage_courses"))
        return super().form_valid(form)


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
                    self.request, "Default bookmark list created successfully."
                )
        except Exception as e:
            messages.error(
                self.request, f"Failed to create default bookmark. Error: {str(e)}"
            )
            logger.error(f"Failed to create default bookmark: {str(e)}")

        if user.role == "training_provider":
            # set user to inactive and redirect to provider verification page
            user.is_active = False
            user.save()
            auth_login(
                self.request,
                user,
                backend="users.backends.TrainingProviderVerificationBackend",
            )
            return redirect("provider_verification")
        else:
            # log in the user and redirect to profile page
            auth_login(
                self.request,
                user,
                backend="allauth.account.auth_backends.AuthenticationBackend",
            )
            return redirect("profile")


@login_required
def profile_view(request):
    logger.debug("Profile view accessed")
    form = None  # Default value

    if request.method == "POST":
        # Handle provider form (training_provider)
        if "provider_form" in request.POST and request.user.role == "training_provider":
            logger.debug("Processing provider form submission")
            provider = getattr(request.user, "provider_profile", None)
            provider_form = ProviderUpdateForm(
                request.POST, request.FILES, instance=provider
            )
            form = ProfileUpdateForm(instance=request.user)

            if provider_form.is_valid():
                provider = provider_form.save(commit=False)

                if "certificate" in request.FILES:
                    if provider.certificate:
                        old_certificate_path = provider.certificate.path
                        provider.certificate = None
                        if os.path.isfile(old_certificate_path):
                            try:
                                os.remove(old_certificate_path)
                            except Exception as e:
                                logger.error(
                                    f"Error deleting old certificate file: {e}"
                                )
                    provider.certificate = request.FILES["certificate"]

                provider.user = request.user
                provider.save()
                return redirect("profile")
            else:
                messages.error(
                    request, f"Error updating profile. {provider_form.errors}"
                )

        # Handle student form (career_changer)
        elif "student_form" in request.POST and request.user.role == "career_changer":
            student_form = StudentProfileForm(
                request.POST, instance=request.user.student_profile
            )
            if student_form.is_valid():
                student_form.save()
                return redirect("profile")
            else:
                messages.error(
                    request, "Error updating profile. Please check your input."
                )

        # Handle user profile form (modal)
        elif request.POST.get("user_profile_form") is not None:
            form = ProfileUpdateForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect("profile")
            else:
                messages.error(
                    request, "Error updating profile. Please check your input."
                )
    else:
        # GET request: populate initial form
        form = ProfileUpdateForm(instance=request.user)

    context = {
        "user": request.user,
        "role": request.user.role,
        "form": form,
    }

    # Provider data
    if request.user.role == "training_provider":
        try:
            provider = Provider.objects.get(user=request.user)
            context["provider"] = provider
            context["provider_update_form"] = ProviderUpdateForm(instance=provider)
        except Provider.DoesNotExist:
            context["provider_update_form"] = ProviderUpdateForm()

    # Career changer data
    elif request.user.role == "career_changer":
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            student = Student.objects.create(user=request.user)
        context["student"] = student
        context["student_form"] = StudentProfileForm(instance=student)

        # Bookmarks
        bookmark_lists = request.user.bookmark_list.all().prefetch_related(
            "bookmark__course"
        )
        context["bookmark_lists"] = bookmark_lists

        # Reviews
        reviews = Review.objects.filter(user=request.user).select_related("course")
        context["reviews"] = reviews
        context["debug"] = False

    return render(request, "users/profile.html", context)


def provider_verification_required(function):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("account_login")

        if getattr(request.user, "role", "") == "training_provider":
            return function(request, *args, **kwargs)
        else:
            return redirect("home")

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


@provider_verification_required
def provider_verification_view(request):
    if request.user.role != "training_provider":
        return redirect("home")
    elif request.user.is_active:
        return redirect("manage_courses")

    if request.method == "POST":
        form = ProviderVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            confirm_existing = form.cleaned_data.get("confirm_existing", False)

            try:
                existing_provider = Provider.objects.get(name=name)
            except Provider.DoesNotExist:
                existing_provider = None

            if (
                existing_provider
                and existing_provider.user is None
                and confirm_existing
            ):
                provider = existing_provider
                provider.user = request.user
                provider.verification_status = False
                provider.save()
            else:
                provider = form.save(commit=False)
                provider.user = request.user
                provider.verification_status = False
                provider.save()

            request.user.is_active = True
            request.user.save()
            auth_login(
                request,
                request.user,
                backend="allauth.account.auth_backends.AuthenticationBackend",
            )

            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    else:
        form = ProviderVerificationForm()

    return render(request, "account/provider_verification.html", {"form": form})


def check_provider_name(request):
    name = request.GET.get("name", "")
    try:
        provider = Provider.objects.get(name=name)
        return JsonResponse(
            {
                "exists": True,
                "user": provider.user_id is not None,
                "details": {
                    "name": provider.name,
                    "address": provider.address,
                    "phone_num": provider.phone_num,
                    "website": provider.website or "",
                    "contact_firstname": provider.contact_firstname or "",
                    "contact_lastname": provider.contact_lastname or "",
                },
            }
        )
    except Provider.DoesNotExist:
        return JsonResponse({"exists": False})


class ProviderDetailView(generic.DetailView):
    model = Provider
    template_name = "profile/provider_detail.html"
    context_object_name = "provider"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["courses"] = self.object.course.all()
        return context


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


@login_required
@require_POST
def add_tag(request):
    try:
        data = json.loads(request.body)
        tag_name = data.get("tag", "").strip().lower()
        if not tag_name:
            return JsonResponse({"success": False, "error": "Tag name is required"})

        student = request.user.student_profile

        # Check if student already has this tag
        if student.tags.filter(name=tag_name).exists():
            return JsonResponse(
                {"success": False, "error": "You already have this tag"}
            )

        tag, created = Tag.objects.get_or_create(name=tag_name)
        student.tags.add(tag)
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def remove_tag(request):
    try:
        data = json.loads(request.body)
        tag_name = data.get("tag", "").strip()
        if not tag_name:
            return JsonResponse({"success": False, "error": "Tag name is required"})

        student = request.user.student_profile
        tag = Tag.objects.filter(name=tag_name.lower()).first()
        if tag:
            student.tags.remove(tag)
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


class CustomPasswordResetView(PasswordResetView):
    template_name = "account/password_reset.html"

    def form_valid(self, form):
        form.save(self.request)

        # Always respond with empty JSON — handled entirely in JS
        return JsonResponse({"success": True})
