from django import forms
from .models import Course


class CourseForm(forms.ModelForm):
    location = forms.CharField(required=False)
    
    class Meta:
        model = Course
        fields = [
            "name",
            "keywords",
            "course_desc",
            "cost",
            "location",
            "classroom_hours",
            "lab_hours",
            "internship_hours",
            "practical_hours",
        ]
