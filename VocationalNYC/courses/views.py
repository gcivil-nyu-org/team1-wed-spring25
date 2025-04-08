import requests
import logging
import re

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Q, Avg, Count
from django.core.cache import cache
from review.models import Review
import hashlib

from users.models import Provider
from .models import Course
from django.http import JsonResponse
from bookmarks.models import BookmarkList


logger = logging.getLogger(__name__)


class CourseListView(generic.ListView):
    model = Course
    template_name = "courses/course_list.html"
    context_object_name = "courses"
    ordering = ["-course_id"]

    def get_queryset(self):
        # Update Api data once a day
        logger.info("Starting course data refresh check")
        API_URL = "https://data.cityofnewyork.us/resource/fgq8-am2v.json"
        if not cache.get("courses_last_updated"):
            try:
                logger.info("Fetching courses from API")
                response = requests.get(API_URL, timeout=10)
                response.raise_for_status()
                courses_data = response.json()

                for course in courses_data:
                    logger.debug(f"Processing course: {course.get('course_name', '')}")
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

                    course_defaults = {
                        "keywords": course.get("keywords", ""),
                        "course_desc": course.get("coursedescription", ""),
                        "cost": course.get("cost_total", 0),
                        "location": location,
                        "classroom_hours": classroom_hours,
                        "lab_hours": lab_hours,
                        "internship_hours": internship_hours,
                        "practical_hours": practical_hours,
                    }
                    
                    # Create or update the course
                    logger.info(f"Updating/creating course: {course_name}")
                    course_obj, created = Course.objects.update_or_create(
                        name=course_name, provider=provider, defaults=course_defaults
                    )
                    logger.info(f"Course {'created' if created else 'updated'}: {course_name}")
                    
                    # Convert keywords to tags
                    if course_defaults["keywords"]:
                        logger.debug(f"Processing tags for course: {course_name}")
                        course_obj.set_keywords_as_tags(course_defaults["keywords"])

                logger.info("Course data refresh completed")
                cache.set("courses_last_updated", True, 86400)

            except requests.RequestException as e:
                logger.error(f"External API call failed: {e}")

        logger.info("Fetching courses from database")
        courses = Course.objects.all().annotate(
            avg_rating=Avg("reviews__score_rating"), reviews_count=Count("reviews")
        )
        logger.info(f"Found {courses.count()} courses")

        for course in courses:
            avg = course.avg_rating if course.avg_rating is not None else 0
            course.rating = round(avg, 1)
            course.rating_full_stars = int(avg)
            if avg - int(avg) > 0:
                course.rating_partial_star_position = course.rating_full_stars + 1
                course.rating_partial_percentage = int((avg - int(avg)) * 100)
            else:
                course.rating_partial_star_position = 0
                course.rating_partial_percentage = 0

        return courses

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            # Add bookmark list data
            user = self.request.user
            if user.is_authenticated:
                bookmark_lists = BookmarkList.objects.filter(user=user)
                default_list = bookmark_lists.first()
            else:
                bookmark_lists = []
                default_list = None

            context["bookmark_lists"] = bookmark_lists
            context["default_bookmark_list"] = default_list
            return context


class CourseDetailView(LoginRequiredMixin, generic.DetailView):
    model = Course
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reviews = Review.objects.filter(course=self.object).order_by("-created_at")
        context["reviews"] = reviews
        return context


def filterCourses(request):
    # query = request.GET.get("query", "").strip()
    keywords = request.GET.get("keywords", "").strip()

    provider_name = request.GET.get("provider", "")
    min_rating = request.GET.get("min_rating", None)
    min_cost = request.GET.get("min_cost", None)
    max_cost = request.GET.get("max_cost", None)
    location = request.GET.get("location", "")
    min_classroom_hours = request.GET.get("min_classroom_hours", None)
    # tags = request.GET.getlist("tags", [])  # Get multiple tag values

    courses = Course.objects.all()

    if keywords:
        courses = courses.filter(
            Q(name__icontains=keywords)
            | Q(course_desc__icontains=keywords)
            | Q(keywords__icontains=keywords)
        )

    if provider_name:
        courses = courses.filter(provider__name__icontains=provider_name)

    if min_cost is not None and min_cost.isdigit():
        courses = courses.filter(cost__gte=int(min_cost))

    if max_cost is not None and max_cost.isdigit():
        courses = courses.filter(cost__lte=int(max_cost))

    if location:
        courses = courses.filter(location__icontains=location)

    if min_classroom_hours is not None and min_classroom_hours.isdigit():
        courses = courses.filter(classroom_hours__gte=int(min_classroom_hours))

    # if tags:
    #     courses = courses.filter(tags__name__in=tags).distinct()

    courses = courses.annotate(
        avg_rating=Avg("reviews__score_rating"), reviews_count=Count("reviews")
    )

    if min_rating and min_rating.replace(".", "", 1).isdigit():
        courses = courses.filter(avg_rating__gte=float(min_rating))

    for course in courses:
        avg = course.avg_rating if course.avg_rating is not None else 0
        course.rating = round(avg, 1)
        course.rating_full_stars = int(avg)
        if avg - int(avg) > 0:
            course.rating_partial_star_position = course.rating_full_stars + 1
            course.rating_partial_percentage = int((avg - int(avg)) * 100)
        else:
            course.rating_partial_star_position = 0
            course.rating_partial_percentage = 0

    context = {
        "courses": courses,
        "keywords": keywords,
        "provider_name": provider_name,
        "min_rating": min_rating,
        "min_cost": min_cost,
        "max_cost": max_cost,
        "location": location,
        "min_classroom_hours": min_classroom_hours,
    }
    return context


def search_result(request):
    context = filterCourses(request)
    return render(request, "courses/course_list.html", context)


GOOGLE_MAPS_API_KEY = "AIzaSyCawC4Ts27j8dsyhx_sw8_EDCCA1UOT5G0"


def get_coordinates(address):
    """Convert an address to latitude and longitude using Google Maps API, with caching."""
    if not address:
        return None, None

    key = "coords:" + hashlib.sha256(address.encode()).hexdigest()

    cached_coords = cache.get(key)
    if cached_coords:
        return cached_coords

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            coords = (location["lat"], location["lng"])
            cache.set(key, coords, timeout=60 * 60 * 24 * 7)  # Cache for 7 days
            return coords
    except requests.RequestException as e:
        logger.error("Geocoding API error: %s", e)

    return None, None


def course_map(request):
    """Render the course map page"""
    return render(request, "courses/course_map.html")


def course_data(request):
    """Fetch course data and get lat/lng dynamically"""
    courses = Course.objects.all()
    course_id = request.GET.get("course_id")

    if course_id and course_id.isdigit():
        courses = courses.filter(course_id=course_id)

    keywords = request.GET.get("keywords")
    min_cost = request.GET.get("min_cost")
    max_cost = request.GET.get("max_cost")
    min_rating = request.GET.get("min_rating")
    provider = request.GET.get("provider")
    location = request.GET.get("location")
    min_hours = request.GET.get("min_hours")

    if keywords:
        courses = courses.filter(Q(name__icontains=keywords))
    if min_cost and min_cost.isdigit():
        courses = courses.filter(cost__gte=int(min_cost))
    if max_cost and max_cost.isdigit():
        courses = courses.filter(cost__lte=int(max_cost))
    if min_hours and min_hours.isdigit():
        courses = courses.filter(classroom_hours__gte=int(min_hours))
    if location:
        courses = courses.filter(location__icontains=location)
    if provider:
        courses = courses.filter(provider__name__icontains=provider)

    courses = courses.annotate(avg_rating=Avg("reviews__score_rating"))
    if min_rating:
        try:
            courses = courses.filter(avg_rating__gte=float(min_rating))
        except ValueError:
            pass

    data = []
    for course in courses:
        lat, lng = get_coordinates(course.location)
        if lat and lng:
            data.append(
                {
                    "course_id": course.course_id,
                    "name": course.name,
                    "course_desc": course.course_desc,
                    "latitude": lat,
                    "longitude": lng,
                }
            )

    return JsonResponse(data, safe=False)


def sort_by(request):

    context = filterCourses(request)
    courses = context["courses"]
    sort = request.GET.get("sort", "blank")
    order = request.GET.get("order", "asc")

    if sort != "blank":
        if order == "desc":
            sort = f"-{sort}"
        courses = courses.order_by(sort)

    # Render full HTML for the page (not just partial updates)
    return render(request, "courses/courses_section.html", {"courses": courses})
