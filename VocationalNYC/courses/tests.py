# import unittest
from unittest.mock import patch
# import json

from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from courses.views import CourseListView
from courses.models import Course
from users.models import Provider
from review.models import Review
from requests.exceptions import RequestException


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"API returned {self.status_code}")


class CourseListViewTest(TestCase):
    @patch("courses.views.requests.get")
    def setUp(self, mock_get):
        self.factory = RequestFactory()
        self.mock_api_response = [
            {
                "course_name": "Test Course",
                "organization_name": "Test Provider",
                "address1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip_code": "12345",
                "phone1": "1234567890",
                "open_time": "9AM-5PM",
                "provider_description": "Test provider description",
                "website": "http://testprovider.com",
                "cost_includes": "Classroom Hours 40 Lab Hours 20 Internship Hours 10 Practical Hours 15",
                "keywords": "test, course, django",
                "coursedescription": "Test course description",
                "cost_total": "1000",
            }
        ]
        mock_get.return_value = MockResponse(self.mock_api_response)

        # Create view instance
        self.view = CourseListView()

    @patch("courses.views.requests.get")
    def test_get_queryset_api_call(self, mock_get):
        mock_get.return_value = MockResponse(self.mock_api_response)

        # Call the method
        courses = self.view.get_queryset()

        # Verify API was called
        mock_get.assert_called_once_with(
            "https://data.cityofnewyork.us/resource/fgq8-am2v.json", timeout=10
        )

        # Verify a course was created
        self.assertEqual(courses.count(), 1)
        course = courses.first()
        self.assertEqual(course.name, "Test Course")

        # Verify provider was created
        provider = Provider.objects.first()
        self.assertEqual(provider.name, "Test Provider")
        self.assertEqual(provider.phone_num, "1234567890")

        # Verify course details
        self.assertEqual(course.classroom_hours, 40)
        self.assertEqual(course.lab_hours, 20)
        self.assertEqual(course.internship_hours, 10)
        self.assertEqual(course.practical_hours, 15)
        self.assertEqual(course.cost, 1000)

    @patch("courses.views.requests.get")
    def test_get_queryset_api_error(self, mock_get):
        mock_get.side_effect = RequestException("API Error")

        # Call the method
        courses = self.view.get_queryset()

        # Should return all courses even if API fails
        self.assertEqual(list(courses), list(Course.objects.all()))

    def test_list_view_template(self):
        response = self.client.get(reverse("course_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courses/course_list.html")
        self.assertIn("courses", response.context)


class CourseDetailViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )

        # Create test provider
        self.provider = Provider.objects.create(
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St, Test City, TS, 12345",
            provider_desc="Test provider description",
            website="http://testprovider.com",
        )

        # Create test course
        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            keywords="test, django",
            course_desc="Test course description",
            cost=1000,
            location="123 Test St, Test City, TS, 12345",
            classroom_hours=40,
            lab_hours=20,
            internship_hours=10,
            practical_hours=15,
        )

        self.review1 = Review.objects.create(
            user=self.user, course=self.course, score_rating=5
        )

        self.review2 = Review.objects.create(
            user=self.user, course=self.course, score_rating=4
        )

        # Create client and login
        self.client = Client()
        self.client.login(username="testuser", password="testpassword")

    def test_detail_view_context_data(self):
        response = self.client.get(
            reverse("course_detail", kwargs={"pk": self.course.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["course"], self.course)
        self.assertQuerySetEqual(
            response.context["reviews"],
            [self.review1, self.review2],
            ordered=False,
            transform=lambda x: x,
        )

    def test_detail_view_template(self):
        response = self.client.get(
            reverse("course_detail", kwargs={"pk": self.course.pk})
        )
        self.assertTemplateUsed(response, "courses/course_detail.html")

    def test_login_required(self):
        # Logout first
        self.client.logout()

        # Try to access the detail page
        response = self.client.get(
            reverse("course_detail", kwargs={"pk": self.course.pk})
        )

        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))


class SearchResultTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Create test providers
        self.provider1 = Provider.objects.create(
            name="Provider One",
            phone_num="1234567890",
            address="123 NYC Street, New York, NY, 10001",
        )

        self.provider2 = Provider.objects.create(
            name="Provider Two",
            phone_num="0987654321",
            address="456 Boston Road, Boston, MA, 02101",
        )

        # Create test courses
        self.course1 = Course.objects.create(
            name="Python Programming",
            provider=self.provider1,
            keywords="python, programming, web",
            course_desc="Learn Python programming language",
            cost=1000,
            location="123 NYC Street, New York, NY, 10001",
            classroom_hours=40,
        )

        self.course2 = Course.objects.create(
            name="Data Science",
            provider=self.provider1,
            keywords="data, python, analytics",
            course_desc="Learn data science with Python",
            cost=2000,
            location="123 NYC Street, New York, NY, 10001",
            classroom_hours=60,
        )

        self.course3 = Course.objects.create(
            name="Web Development",
            provider=self.provider2,
            keywords="web, html, css",
            course_desc="Learn web development basics",
            cost=800,
            location="456 Boston Road, Boston, MA, 02101",
            classroom_hours=30,
        )

    def test_search_by_name(self):
        response = self.client.get(reverse("search_result"), {"query": "Python"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 2)
        self.assertIn(self.course1, response.context["courses"])
        self.assertIn(self.course2, response.context["courses"])

    def test_search_by_description(self):
        response = self.client.get(reverse("search_result"), {"query": "data science"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 1)
        self.assertEqual(response.context["courses"][0], self.course2)

    def test_search_by_keywords(self):
        response = self.client.get(reverse("search_result"), {"query": "web"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 2)
        self.assertIn(self.course1, response.context["courses"])
        self.assertIn(self.course3, response.context["courses"])

    def test_filter_by_cost(self):
        response = self.client.get(
            reverse("search_result"), {"min_cost": "900", "max_cost": "1500"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 1)
        self.assertEqual(response.context["courses"][0], self.course1)

    def test_filter_by_location(self):
        response = self.client.get(reverse("search_result"), {"location": "Boston"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 1)
        self.assertEqual(response.context["courses"][0], self.course3)

    def test_filter_by_classroom_hours(self):
        response = self.client.get(
            reverse("search_result"), {"min_classroom_hours": "50"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 1)
        self.assertEqual(response.context["courses"][0], self.course2)

    def test_combined_search_and_filters(self):
        response = self.client.get(
            reverse("search_result"),
            {
                "q": "python",
                "min_cost": "1500",
                "max_cost": "2500",
                "location": "New York",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 1)
        self.assertEqual(response.context["courses"][0], self.course2)

    def test_empty_search(self):
        response = self.client.get(reverse("search_result"), {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 3)
