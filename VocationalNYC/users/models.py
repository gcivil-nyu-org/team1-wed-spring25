from django.db import models
from .managers import CustomUserManager
from django.contrib.auth.models import AbstractUser
import uuid


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


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="student_profile"
    )
    bio = models.TextField(blank=True, null=True, max_length=1000)
    tags = models.ManyToManyField(Tag, related_name="student", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def modify_profile(self, bio=None):
        """
        Modify the student's profile information
        """
        if bio is not None:
            self.bio = bio
        self.save()
        return self

    def add_tag(self, tag):
        """
        Add a single tag to student's interests
        """
        if tag not in self.tags.all():
            self.tags.add(tag)
            self.save()
        return self

    def remove_tag(self, tag):
        """
        Remove a single tag from student's interests
        """
        if tag in self.tags.all():
            self.tags.remove(tag)
            self.save()
        return self

    class Meta:
        verbose_name = "Career Changer"
        verbose_name_plural = "Career Changers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Student: {self.user.username}"


def certificate_file_path(instance, filename):
    # Generate a unique filename using UUID
    ext = filename.split(".")[-1]
    filename = f"certificate_{uuid.uuid4().hex}.{ext}"
    return f"provider_certificates/{filename}"


class Provider(models.Model):
    provider_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
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
    certificate = models.FileField(
        upload_to=certificate_file_path,
        null=True,
        blank=True,
        help_text="Upload your business certificate (PDF, JPG, PNG). Size limit: 5MB",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Training Provider"
        verbose_name_plural = "Training Providers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.website}"
