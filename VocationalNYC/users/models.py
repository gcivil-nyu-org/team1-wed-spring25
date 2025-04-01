from django.db import models
from .managers import CustomUserManager
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ("career_changer", "Career Changer"),
        ("training_provider", "Training Provider"),
        ("administrator", "Administrator"),
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="career_changer"
    )
    time_created = models.DateTimeField(auto_now_add=True)
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.role.capitalize()}: {self.username}"


class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="student_profile"
    )
    bio = models.TextField(blank=True, null=True)
    tag = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Career Changer"
        verbose_name_plural = "Career Changers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Student: {self.user.username}"


class Provider(models.Model):
    provider_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="provider_profile",
    )
    name = models.CharField(max_length=255, unique=True)
    contact_firstname = models.CharField(max_length=255, blank=True, null=True)
    contact_lastname = models.CharField(max_length=255, blank=True, null=True)
    phone_num = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    open_time = models.CharField(max_length=100, null=True, blank=True)
    provider_desc = models.TextField(null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    verification_status = models.BooleanField(default=False)
    verification_file_url = models.URLField(blank=True, null=True)
    verification_file = models.FileField(
        upload_to="provider_certificates/",
        null=True,
        blank=True,
        help_text="Upload your business certificate (PDF, JPG, PNG)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Training Provider"
        verbose_name_plural = "Training Providers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.website}"
