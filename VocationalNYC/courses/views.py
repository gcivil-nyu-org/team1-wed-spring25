import requests
import logging
import re

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Q

from users.models import Provider
from .models import Course, CourseDuration

logger = logging.getLogger(__name__)


class CourseListView(generic.ListView):
    model = Course
    template_name = "courses/course_list.html"
    context_object_name = "courses"
    ordering = ["-course_id"]

    def get_queryset(self):
        # Only update from the external API if no courses exist.
        if not Course.objects.exists():
            API_URL = "https://data.cityofnewyork.us/resource/fgq8-am2v.json"
            try:
                response = requests.get(API_URL, timeout=10)
                response.raise_for_status()
                courses_data = response.json()

                for course in courses_data:
                    course_name = course.get("course_name", "").strip()
                    provider_name = course.get("organization_name", "").strip()

                    if not course_name or not provider_name:
                        continue

                    address1 = course.get("address1", "").strip()
                    city = course.get("city", "").strip()
                    state = course.get("state", "").strip()
                    zip_code = course.get("zip_code", "").strip()

                    location = ", ".join(
                        filter(None, [address1, city, state, zip_code])
                    )

                    # Get or create the provider
                    provider, created = Provider.objects.get_or_create(
                        name=provider_name,
                        defaults={
                            "phone_num": course.get("phone1", "0000000000"),
                            "address": location,
                            "open_time": course.get("open_time", ""),
                            "provider_desc": course.get("provider_description", ""),
                            "website": course.get("website", ""),
                        },
                    )

                    # check whether course exists
                    if not Course.objects.filter(
                        name=course_name, provider=provider
                    ).exists():
                        new_course = Course.objects.create(
                            name=course_name,
                            provider=provider,
                            keywords=course.get("keywords", ""),
                            course_desc=course.get("coursedescription", ""),
                            cost=course.get("cost_total", 0),
                            location=location,
                        )

                    duration = course.get("cost_includes", "").strip()

                    classroom_match = re.search(
                        r"Classroom Hours\s+(\d+\.?\d*)", duration
                    )
                    classroom_hours = (
                        int(float(classroom_match.group(1))) if classroom_match else 0
                    )

                    lab_match = re.search(r"Lab Hours\s+(\d+\.?\d*)", duration)
                    lab_hours = int(float(lab_match.group(1))) if lab_match else 0

                    internship_match = re.search(
                        r"Internship Hours\s+(\d+\.?\d*)", duration
                    )
                    internship_hours = (
                        int(float(internship_match.group(1))) if internship_match else 0
                    )

                    practical_match = re.search(
                        r"Practical Hours\s+(\d+\.?\d*)", duration
                    )
                    practical_hours = (
                        int(float(practical_match.group(1))) if practical_match else 0
                    )

                    # Create the CourseDuration object
                    CourseDuration.objects.create(
                        course=new_course,
                        classroom_hours=classroom_hours,
                        lab_hours=lab_hours,
                        internship_hours=internship_hours,
                        practical_hours=practical_hours,
                    )

            except requests.RequestException as e:
                logger.error("External API call failed: %s", e)

        return Course.objects.all()


class CourseDetailView(LoginRequiredMixin, generic.DetailView):
    model = Course
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_duration = CourseDuration.objects.filter(course=self.object).first()
        context["course_duration"] = course_duration
        return context


def search_result(request):
    query = request.GET.get("q", "").strip()

    min_cost = request.GET.get("min_cost", None)
    max_cost = request.GET.get("max_cost", None)
    location = request.GET.get("location", "")
    min_classroom_hours = request.GET.get("min_classroom_hours", None)

    courses = Course.objects.all()

    print("Query:", query)
    print(
        "min_cost:",
        min_cost,
        "max_cost:",
        max_cost,
        "location:",
        location,
        "min_classroom_hours:",
        min_classroom_hours,
    )

    if query:
        courses = courses.filter(
            Q(name__icontains=query)
            | Q(course_desc__icontains=query)
            | Q(keywords__icontains=query)
        )

    if min_cost is not None and min_cost.isdigit():
        courses = courses.filter(cost__gte=int(min_cost))

    if max_cost is not None and max_cost.isdigit():
        courses = courses.filter(cost__lte=int(max_cost))

    if location:
        courses = courses.filter(location__icontains=location)

    if min_classroom_hours is not None and min_classroom_hours.isdigit():
        courses = courses.filter(
            courseduration__classroom_hours__gte=int(min_classroom_hours)
        )

    context = {
        "courses": courses,
        "query": query,
        "min_cost": min_cost,
        "max_cost": max_cost,
        "location": location,
        "min_classroom_hours": min_classroom_hours,
    }

    return render(request, "courses/course_list.html", context)
