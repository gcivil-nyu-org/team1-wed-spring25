from django.db import models
from users.models import Provider


# Create your models here.
class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    keywords = models.CharField(max_length=255, null=True, blank=True)
    course_desc = models.TextField()
    cost = models.IntegerField(default=0)
    location = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class CourseDuration(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    classroom_hours = models.IntegerField()
    lab_hours = models.IntegerField()
    internship_hours = models.IntegerField()
    practical_hours = models.IntegerField()

    def __str__(self):
        return f"Classroom Hours {self.classroom_hours}, Lab Hours {self.lab_hours}, Internship Hours {self.internship_hours}, Practical Hours {self.practical_hours}."
