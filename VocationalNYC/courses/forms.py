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

        def __init__(self, *args, **kwargs):
            self.provider = kwargs.pop('provider', None)
            super().__init__(*args, **kwargs)
        
        def clean_location(self):
            location = self.cleaned_data.get('location', '')
            if not location or location.strip() == "":
                if self.provider and hasattr(self.provider, 'address'):
                    return self.provider.address
                else:
                    return location
            return location
