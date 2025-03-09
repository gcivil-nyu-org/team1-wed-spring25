from django.db import models
from .managers import CustomUserManager
from django.contrib.auth.models import AbstractUser

class Provider(models.Model):
    provider_id = models.AutoField(primary_key=True)
    # user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    # email = models.EmailField(unique=True)
    phone_num = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    open_time = models.CharField(max_length=100)
    provider_desc = models.TextField()
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.website}"


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
