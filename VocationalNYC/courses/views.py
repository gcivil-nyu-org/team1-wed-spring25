import requests
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic
from users.models import Provider
from .models import Course

logger = logging.getLogger(__name__)


class CourseListView(generic.ListView):
    model = Course
    template_name = "courses/course_list.html" 
    context_object_name = "courses"
    ordering = ["-course_id"]
    
    def get_queryset(self):
        # Only update from the external API if no courses exist.
        if not Course.objects.exists():
            API_URL = 'https://data.cityofnewyork.us/resource/fgq8-am2v.json'
            try:
                response = requests.get(API_URL, timeout=10)
                response.raise_for_status()
                courses_data = response.json()  

                for course in courses_data:
                    course_name = course.get("course_name", "").strip()
                    provider_name = course.get("organization_name", "").strip()

                    if not course_name or not provider_name:
                        continue
                    
                    # Get or create the provider
                    provider, created = Provider.objects.get_or_create(
                        name=provider_name,
                        defaults={
                            "phone_num": course.get("phone1", "0000000000"),
                            "address": course.get("address1", "Unknown"),
                            "open_time": course.get("open_time", "N/A"),
                            "provider_desc": course.get("provider_description", "No description"),
                            "website": course.get("website", ""),
                        }
                    )

                    # check whether provider exists
                    if not Course.objects.filter(name=course_name, provider=provider).exists():
                        Course.objects.create(
                            name=course_name,
                            provider=provider,
                            course_desc=course.get("coursedescription", "No description"),
                            time=course.get("time", "N/A"),
                            location=course.get("address1", "Unknown")
                        )
            except requests.RequestException as e:
                logger.error("External API call failed: %s", e)

        return Course.objects.all()


class CourseDetailView(LoginRequiredMixin, generic.DetailView):
    model = Course
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    login_url = reverse_lazy('account_login')
    redirect_field_name = 'next'
