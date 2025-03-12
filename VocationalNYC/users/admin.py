from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Provider, Student


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_superuser")
    list_filter = ("role", "is_superuser", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")

    def get_queryset(self, request):
        # Filter out provider and student users from main user list
        return (
            super()
            .get_queryset(request)
            .exclude(role__in=["training_provider", "career_changer"])
        )


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        "provider_id",
        "user_id",
        "name",
        "contact_firstname",
        "contact_lastname",
        "phone_num",
        "verification_status",
        "created_at",
    )
    list_filter = ("verification_status", "created_at")
    search_fields = ("name", "contact_firstname", "contact_lastname", "provider_desc")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "contact_firstname", "contact_lastname", "phone_num")},
        ),
        ("Location & Hours", {"fields": ("address", "open_time", "website")}),
        ("Description", {"fields": ("provider_desc",)}),
        ("Verification", {"fields": ("verification_status", "verification_file_url")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "bio", "tag", "created_at")
    list_filter = ("created_at", "tag")
    search_fields = ("user__username", "user__email", "bio")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User Information", {"fields": ("user",)}),
        ("Profile Details", {"fields": ("bio", "tag")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
