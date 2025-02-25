import requests
from django.shortcuts import render
from django.views import generic

from .models import Course
from users.models import Provider

class CourseListView(generic.ListView):
    model = Course
    template_name = "courses/course_list.html" 
    context_object_name = "courses"
    ordering = ["-course_id"]

    def get_queryset(self):
        API_URL = 'https://data.cityofnewyork.us/resource/fgq8-am2v.json'
        response = requests.get(API_URL)
        if response.status_code == 200:
            courses_data = response.json()  

            for course in courses_data:
                course_name = course.get("course_name", "").strip()
                provider_name = course.get("organization_name", "").strip()

                if not course_name or not provider_name:
                    continue  # skip invalid data

                # check whether provider exists
                provider, created = Provider.objects.get_or_create(name=provider_name, defaults={
                    "phone_num": course.get("phone1", "0000000000"),
                    "address": course.get("address1", "Unknown"),
                    "open_time": course.get("open_time", "N/A"),
                    "provider_desc": course.get("provider_description", "No description"),
                    "website": course.get("website", ""),
                })

                # check whether course exists
                exists = Course.objects.filter(name=course_name, provider=provider).exists()
                if not exists:
                    Course.objects.create(
                        name=course_name,
                        provider=provider,
                        course_desc=course.get("coursedescription", "No description"),
                        time=course.get("time", "N/A"),
                        location=course.get("address1", "Unknown")
                    )

        else:
            print(f"Call API failed, the status code is: {response.status_code}")

        return Course.objects.all()
