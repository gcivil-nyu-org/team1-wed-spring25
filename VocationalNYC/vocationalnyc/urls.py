"""
URL configuration for vocationalnyc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from views import custom_404


def root_redirect(request):
    if (
        hasattr(request, "user")
        and request.user.is_authenticated
        and (request.user.is_superuser or request.user.is_staff)
    ):
        return redirect("admin:index")
    return redirect("course_list")


# from allauth.account.decorators import secure_admin_login

admin.autodiscover()
# admin.site.login = secure_admin_login(admin.site.login)

urlpatterns = [
    # Root URL now uses our custom redirect view
    path("", root_redirect, name="home"),
    # Account-related URLs
    path("accounts/", include("users.urls")),
    path("", include("users.urls")),
    # Admin URLs
    path(
        "admin/login/",
        auth_views.LoginView.as_view(
            template_name="admin/login.html", next_page="/admin/"
        ),
        name="admin_login",
    ),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # Course app URLs
    path("courses/", include("courses.urls")),
    path("reviews/", include("review.urls")),
    path("chat/", include("message.urls")),
    path("bookmarks/", include("bookmarks.urls")),
    path("404/", custom_404),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
