from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Provider, Student
from django.utils.html import format_html


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
        "name",
        "verification_status",
        "certificate_link",  # custom method, see below
        "created_at",
    )
    # Let the first or second column act as the link to the detail page:
    list_display_links = ("provider_id", "name")
    # Let verification_status be editable from the list:
    list_editable = ("verification_status",)

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
        # Make sure 'certificate' is in your form so it can be uploaded/edited
        ("Verification", {"fields": ("verification_status", "certificate")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def certificate_link(self, obj):
        """
        Return a clickable link to the certificate if it exists,
        otherwise return a dash.
        """
        if obj.certificate:
            return format_html(
                "<a href='{}' target='_blank'>View</a>", obj.certificate.url
            )
        return "-"

    certificate_link.short_description = "Certificate"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "bio", "get_tags_display", "created_at")
    list_filter = ("created_at", "tags")
    search_fields = ("user__username", "user__email", "bio")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User Information", {"fields": ("user",)}),
        ("Profile Details", {"fields": ("bio", "tags")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_tags_display(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    get_tags_display.short_description = "Tags"
