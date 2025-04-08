from django.db import models
from users.models import Provider

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

# Create your models here.
class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="course"
    )
    keywords = models.CharField(max_length=255, null=True, blank=True)
    course_desc = models.TextField()
    cost = models.IntegerField(default=0)
    location = models.CharField(max_length=255)
    classroom_hours = models.IntegerField(default=0)
    lab_hours = models.IntegerField(default=0)
    internship_hours = models.IntegerField(default=0)
    practical_hours = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag, related_name='courses', blank=True)

    def __str__(self):
        return f"{self.name}"
