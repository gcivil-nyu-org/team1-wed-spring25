from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    list_display = ("username", "email", "role", "is_superuser")
    list_filter = ("role", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("email", "first_name", "last_name")}),
        ("Roles & Permissions", {"fields": ("role", "is_superuser", "is_active")}),
    )
