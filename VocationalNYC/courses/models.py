from django.db import models
from users.models import Provider

# Create your models here.
class Course(models.Model):
    course_id = models.AutoField(primary_key=True)  
    name = models.CharField(max_length=255) 
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    keywords = models.CharField(max_length=255, null=True, blank=True) 
    course_desc = models.TextField()
    time = models.CharField(max_length=100)
    location = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"
