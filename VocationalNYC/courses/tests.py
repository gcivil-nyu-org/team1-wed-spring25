# import unittest
from unittest.mock import patch

# import json

from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from courses.views import CourseListView, sort_by, filterCourses
from courses.models import Course
from users.models import CustomUser, Provider
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

    def test_course_tags_operations(self):
        provider = Provider.objects.create(
            name="Test Provider",
            phone_num="1234567890",
            address="Test Address",
        )
        course = Course.objects.create(
            name="Test Course",
            provider=provider,
            course_desc="Test Description",
            cost=1000,
            location="Test Location",
        )

        # Test setting keywords as tags
        course.set_keywords_as_tags("python django testing")
        self.assertEqual(course.tags.count(), 3)
        self.assertTrue(course.tags.filter(name="python").exists())
        self.assertTrue(course.tags.filter(name="django").exists())
        self.assertTrue(course.tags.filter(name="testing").exists())

        # Test getting tags list
        tags_list = course.get_tags_list()
        self.assertEqual(len(tags_list), 3)
        self.assertEqual(
            {tag.name for tag in tags_list}, {"python", "django", "testing"}
        )

        # Test updating keywords and tags (should add new tags without duplicating existing ones)
        course.set_keywords_as_tags("python react frontend")
        self.assertEqual(
            course.tags.count(), 5
        )  # Now 5: python, django, testing, react, frontend
        self.assertTrue(course.tags.filter(name="react").exists())
        self.assertTrue(course.tags.filter(name="frontend").exists())

        # Test empty keywords
        course.set_keywords_as_tags("")
        self.assertEqual(course.tags.count(), 5)  # should not change existing tags

        # Test single character keywords (should be ignored)
        course.set_keywords_as_tags("a b c python")
        self.assertEqual(course.tags.count(), 5)  # only python exists, a,b,c ignored


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
        self.assertTrue(response.url.startswith("/login/"))  # Updated login URL check


def mock_filterCourses(request):
    # Create test provider
    provider = Provider.objects.create(
        name="Test Provider",
        phone_num="1234567890",
        address="123 Test St, New York, NY, 10001",
    )

    # Create test courses
    Course.objects.create(
        name="Course A",
        provider=provider,
        cost=1000,
        classroom_hours=40,
        location="123 Test St, New York, NY, 10001",
    )

    Course.objects.create(
        name="Course B",
        provider=provider,
        cost=2000,
        classroom_hours=60,
        location="456 Test Ave, Brooklyn, NY, 11201",
    )

    Course.objects.create(
        name="Course C",
        provider=provider,
        cost=1500,
        classroom_hours=50,
        location="789 Test Blvd, Queens, NY, 11301",
    )

    return {"courses": Course.objects.all()}


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
        response = self.client.get(reverse("search_result"), {"keywords": "Python"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 2)
        self.assertIn(self.course1, response.context["courses"])
        self.assertIn(self.course2, response.context["courses"])

    def test_search_by_description(self):
        response = self.client.get(
            reverse("search_result"), {"keywords": "data science"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 1)
        self.assertEqual(response.context["courses"][0], self.course2)

    def test_search_by_keywords(self):
        response = self.client.get(reverse("search_result"), {"keywords": "web"})
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

    def test_filter_by_total_hours(self):
        response = self.client.get(reverse("search_result"), {"min_hours": "50"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["courses"]), 1)
        self.assertEqual(response.context["courses"][0], self.course2)

    def test_combined_search_and_filters(self):
        response = self.client.get(
            reverse("search_result"),
            {
                "keywords": "python",
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

    @patch("courses.views.filterCourses", side_effect=mock_filterCourses)
    def test_sort_by_function_default_order(self, mock_filter_courses):
        # Create a request without sorting parameters (default behavior)
        request = self.factory.get("/courses/sort/")

        # Call the sort_by function
        response = sort_by(request)

        # Verify the response is rendered correctly
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")

        # Check that the response contains all courses
        content = response.content.decode("utf-8")
        self.assertIn("Course A", content)
        self.assertIn("Course B", content)
        self.assertIn("Course C", content)


class FilterCoursesTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )

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

    def test_filter_by_keywords_name(self):
        request = self.factory.get("/search/", {"keywords": "Python"})
        request.user = self.user
        context = filterCourses(request)
        self.assertEqual(len(context["courses"]), 2)
        self.assertIn(self.course1, context["courses"])
        self.assertIn(self.course2, context["courses"])

    def test_filter_by_keywords_description(self):
        request = self.factory.get("/search/", {"keywords": "data science"})
        request.user = self.user
        context = filterCourses(request)
        self.assertEqual(len(context["courses"]), 1)
        self.assertEqual(context["courses"][0], self.course2)

    def test_filter_by_keywords_keywords(self):
        request = self.factory.get("/search/", {"keywords": "web"})
        request.user = self.user
        context = filterCourses(request)
        self.assertEqual(len(context["courses"]), 2)
        self.assertIn(self.course1, context["courses"])
        self.assertIn(self.course3, context["courses"])

    def test_filter_by_provider(self):
        request = self.factory.get("/search/", {"provider": "Provider One"})
        request.user = self.user
        context = filterCourses(request)
        self.assertEqual(len(context["courses"]), 2)
        self.assertIn(self.course1, context["courses"])
        self.assertIn(self.course2, context["courses"])

    def test_filter_by_cost_range(self):
        request = self.factory.get("/search/", {"min_cost": "900", "max_cost": "1500"})
        request.user = self.user
        context = filterCourses(request)
        self.assertEqual(len(context["courses"]), 1)
        self.assertEqual(context["courses"][0], self.course1)

    def test_filter_by_location(self):
        request = self.factory.get("/search/", {"location": "Boston"})
        request.user = self.user
        context = filterCourses(request)
        self.assertEqual(len(context["courses"]), 1)
        self.assertEqual(context["courses"][0], self.course3)

    def test_filter_by_classroom_hours(self):
        request = self.factory.get("/search/", {"min_hours": "50"})
        request.user = self.user
        context = filterCourses(request)
        self.assertEqual(len(context["courses"]), 1)
        self.assertEqual(context["courses"][0], self.course2)

    def test_combined_filters(self):
        request = self.factory.get(
            "/search/",
            {
                "keywords": "python",
                "min_cost": "1500",
                "max_cost": "2500",
                "location": "New York",
            },
        )
        request.user = self.user
        context = filterCourses(request)
        self.assertEqual(len(context["courses"]), 1)
        self.assertEqual(context["courses"][0], self.course2)

    def test_no_filters(self):
        request = self.factory.get("/search/")
        request.user = self.user
        context = filterCourses(request)
        self.assertEqual(len(context["courses"]), 3)
        self.assertIn(self.course1, context["courses"])
        self.assertIn(self.course2, context["courses"])
        self.assertIn(self.course3, context["courses"])


class CourseMapTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()

        # Create test provider and course
        self.provider = Provider.objects.create(
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St, New York, NY, 10001",
        )

        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            location="123 Test St, New York, NY, 10001",
        )

    def test_course_map_view(self):
        response = self.client.get(reverse("course_map"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courses/course_map.html")

    @patch("courses.views.requests.get")
    def test_course_data_view(self, mock_get):
        mock_get.return_value = MockResponse(
            {
                "status": "OK",
                "results": [
                    {"geometry": {"location": {"lat": 40.7128, "lng": -74.0060}}}
                ],
            }
        )

        response = self.client.get(reverse("course_data"))
        self.assertEqual(response.status_code, 200)

        # Parse the JSON response
        response_data = response.json()

        # Verify the response data structure
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["name"], "Test Course")
        self.assertEqual(response_data[0]["course_id"], self.course.course_id)
        self.assertEqual(response_data[0]["course_desc"], "")
        self.assertEqual(response_data[0]["latitude"], 40.7128)
        self.assertEqual(response_data[0]["longitude"], -74.0060)


class PostNewCourseTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()

        # Create test user with training_provider role
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="training_provider",  # Set the role to training_provider
        )

        # Create provider profile for the user
        self.provider = Provider.objects.create(
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St, New York, NY, 10001",
            user=self.user,  # Link the provider to the user
        )

        self.client.login(username="testuser", password="testpass123")

    # def test_post_new_course_post_valid(self):
    #     data = {
    #         "name": "New Test Course",
    #         "keywords": "test, course",
    #         "course_desc": "Test course description",
    #         "cost": 1000,
    #         "location": "123 Test St, New York, NY, 10001",
    #         "classroom_hours": 40,
    #         "lab_hours": 20,
    #         "internship_hours": 10,
    #         "practical_hours": 15,
    #     }

    #     response = self.client.post(reverse("new_course"), data)
    #     self.assertEqual(response.status_code, 302)  # Should redirect
    #     self.assertTrue(Course.objects.filter(name="New Test Course").exists())

    # def test_post_new_course_post_invalid(self):
    #     data = {
    #         "name": "",  # Invalid: empty name
    #         "course_desc": "Test course description",
    #         "cost": -100,  # Invalid: negative cost
    #         "location": "123 Test St, New York, NY, 10001",
    #         "classroom_hours": -40,  # Invalid: negative hours
    #         "lab_hours": 20,
    #     }

    #     response = self.client.post(reverse("new_course"), data)
    #     self.assertEqual(response.status_code, 200)  # Should stay on form page
    #     self.assertFalse(
    #         Course.objects.filter(course_desc="Test course description").exists()
    #     )


# class CourseListViewBookmarksTest(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#         self.client = Client()

#         # Create test user
#         self.user = get_user_model().objects.create_user(
#             username='testuser',
#             email='test@example.com',
#             password='testpass123'
#         )

#         # Create test provider and course
#         self.provider = Provider.objects.create(
#             name="Test Provider",
#             phone_num="1234567890",
#             address="123 Test St, New York, NY, 10001"
#         )

#         self.course = Course.objects.create(
#             name="Test Course",
#             provider=self.provider,
#             location="123 Test St, New York, NY, 10001"
#         )

#         self.client.login(username='testuser', password='testpass123')

#     def test_context_with_bookmarks(self):
#         # Create a bookmark list
#         from bookmarks.models import BookmarkList
#         bookmark_list = BookmarkList.objects.create(
#             user=self.user,
#             name="My Bookmarks"
#         )

#         response = self.client.get(reverse('course_list'))
#         self.assertEqual(response.status_code, 200)
#         self.assertIn('bookmark_lists', response.context)
#         self.assertIn('default_bookmark_list', response.context)
#         self.assertEqual(response.context['default_bookmark_list'], bookmark_list)

#     def test_context_without_bookmarks(self):
#         response = self.client.get(reverse('course_list'))
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(list(response.context['bookmark_lists']), [])
#         self.assertIsNone(response.context['default_bookmark_list'])


class SortByFunctionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user = get_user_model().objects.create_user(
            username="sortuser", email="sort@example.com", password="testpass"
        )

        # Create test courses
        self.course1 = Course.objects.create(
            name="Course A",
            provider=Provider.objects.create(name="Provider A"),
            cost=1000,
            classroom_hours=40,
        )
        self.course2 = Course.objects.create(
            name="Course B",
            provider=Provider.objects.create(name="Provider B"),
            cost=2000,
            classroom_hours=60,
        )
        self.course3 = Course.objects.create(
            name="Course C",
            provider=Provider.objects.create(name="Provider C"),
            cost=800,
            classroom_hours=30,
        )

    def test_sort_by_name_ascending(self):
        request = self.factory.get("/courses/sort/", {"sort": "name", "order": "asc"})
        request.user = self.user
        response = sort_by(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("Course A", content)
        self.assertIn("Course B", content)
        self.assertIn("Course C", content)
        # Verify order in content
        a_index = content.find("Course A")
        b_index = content.find("Course B")
        c_index = content.find("Course C")
        self.assertTrue(a_index < b_index < c_index)

    def test_sort_by_name_descending(self):
        request = self.factory.get("/courses/sort/", {"sort": "name", "order": "desc"})
        request.user = self.user
        response = sort_by(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("Course A", content)
        self.assertIn("Course B", content)
        self.assertIn("Course C", content)
        # Verify order in content
        a_index = content.find("Course A")
        b_index = content.find("Course B")
        c_index = content.find("Course C")
        self.assertTrue(c_index < b_index < a_index)

    def test_sort_by_cost_ascending(self):
        request = self.factory.get("/courses/sort/", {"sort": "cost", "order": "asc"})
        request.user = self.user
        response = sort_by(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("Course A", content)
        self.assertIn("Course B", content)
        self.assertIn("Course C", content)
        # Verify order in content
        a_index = content.find("Course A")
        b_index = content.find("Course B")
        c_index = content.find("Course C")
        self.assertTrue(c_index < a_index < b_index)

    def test_sort_by_cost_descending(self):
        request = self.factory.get("/courses/sort/", {"sort": "cost", "order": "desc"})
        request.user = self.user
        response = sort_by(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("Course A", content)
        self.assertIn("Course B", content)
        self.assertIn("Course C", content)
        # Verify order in content
        a_index = content.find("Course A")
        b_index = content.find("Course B")
        c_index = content.find("Course C")
        self.assertTrue(b_index < a_index < c_index)

    def test_sort_by_classroom_hours_ascending(self):
        request = self.factory.get(
            "/courses/sort/", {"sort": "classroom_hours", "order": "asc"}
        )
        request.user = self.user
        response = sort_by(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("Course A", content)
        self.assertIn("Course B", content)
        self.assertIn("Course C", content)
        # Verify order in content
        a_index = content.find("Course A")
        b_index = content.find("Course B")
        c_index = content.find("Course C")
        self.assertTrue(c_index < a_index < b_index)

    def test_sort_by_classroom_hours_descending(self):
        request = self.factory.get(
            "/courses/sort/", {"sort": "classroom_hours", "order": "desc"}
        )
        request.user = self.user
        response = sort_by(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        content = response.content.decode("utf-8")
        self.assertIn("Course A", content)
        self.assertIn("Course B", content)
        self.assertIn("Course C", content)
        # Verify order in content
        a_index = content.find("Course A")
        b_index = content.find("Course B")
        c_index = content.find("Course C")
        self.assertTrue(b_index < a_index < c_index)

    # @patch("courses.views.filterCourses", side_effect=mock_filterCourses)
    # def test_sort_by_function_invalid_field(self, mock_filter_courses):
    #     # Create a request with invalid sort field
    #     request = self.factory.get("/courses/sort/", {"sort": "invalid_field", "order": "asc"})

    #     # Call the sort_by function
    #     response = sort_by(request)

    #     # Verify the response is rendered correctly
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    #     # Check that the response contains all courses (default order)
    #     content = response.content.decode('utf-8')
    #     self.assertIn("Course A", content)
    #     self.assertIn("Course B", content)
    #     self.assertIn("Course C", content)

    #     # Verify that the courses are in their original order (not sorted by invalid field)
    #     courses = list(response.context["courses"])
    #     self.assertEqual(len(courses), 3)
    #     self.assertEqual(courses[0].name, "Course A")
    #     self.assertEqual(courses[1].name, "Course B")
    #     self.assertEqual(courses[2].name, "Course C")


class ManageCourseTest(TestCase):
    def setUp(self):
        """
        Set up test data before each test method
        """
        # Create a test user
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )

        # Create a provider profile for the test user
        self.provider = Provider.objects.create(
            user=self.user, name="Test Provider", address="123 Test Street"
        )
        # Create test courses
        self.course1 = Course.objects.create(
            provider=self.provider,
            name="Test Course 1",
            course_desc="Description 1",
            cost=100,
            classroom_hours=10,
            lab_hours=5,
            internship_hours=2,
            practical_hours=3,
            location=self.provider.address,
        )

        self.course2 = Course.objects.create(
            provider=self.provider,
            name="Test Course 2",
            course_desc="Description 2",
            cost=200,
            classroom_hours=15,
            lab_hours=10,
            internship_hours=5,
            practical_hours=5,
            location="Different Location",
        )

        # Create some reviews for the courses
        Review.objects.create(
            course=self.course1,
            user=self.user,
            score_rating=5.0,
            content="Test review content",
        )

        Review.objects.create(
            course=self.course1,
            user=self.user,
            score_rating=4.0,
            content="Test review content",
        )

        # Setup client for making requests
        self.client = Client()

        # Login the test user
        self.client.login(username="testuser", password="testpassword")

    def test_manage_courses_authenticated_provider(self):
        """Test manage_courses view when user is authenticated and has a provider profile"""
        response = self.client.get(reverse("manage_courses"))

        # Check that response is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check that correct template is used
        self.assertTemplateUsed(response, "courses/manage_courses.html")

        # Check that context contains courses and provider
        self.assertIn("courses", response.context)
        self.assertIn("provider", response.context)

        # Check that the correct provider is in the context
        self.assertEqual(response.context["provider"], self.provider)

        # Check that all courses for this provider are included
        self.assertEqual(len(response.context["courses"]), 2)

        # Check that average rating is calculated correctly
        for course in response.context["courses"]:
            if course.pk == self.course1.pk:
                self.assertEqual(course.rating, 4.5)  # (5.0 + 4.0) / 2 = 4.5
                self.assertEqual(course.total_hours, 20)  # 10 + 5 + 2 + 3 = 20
            elif course.pk == self.course2.pk:
                self.assertEqual(course.rating, 0)  # No reviews
                self.assertEqual(course.total_hours, 35)  # 15 + 10 + 5 + 5 = 35

    def test_manage_courses_without_provider_profile(self):
        """Test manage_courses view when user doesn't have a provider profile"""
        # Create a new user without a provider profile
        CustomUser.objects.create_user(
            username="noprovider",
            email="noprovider@example.com",
            password="testpassword",
        )

        # Login the new user
        self.client.login(username="noprovider", password="testpassword")

        # Access the manage_courses view
        response = self.client.get(reverse("manage_courses"))

        # Should redirect to home
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "You do not have a training provider profile."
        )

    def test_post_new_course_get(self):
        """Test GET request to post_new_course view"""
        response = self.client.get(reverse("new_course"))

        # Check that response redirects to manage_courses
        self.assertRedirects(response, reverse("manage_courses"))

    def test_post_new_course_post_valid(self):
        """Test POST request to post_new_course view with valid data"""
        # Data for the new course
        course_data = {
            "name": "New Test Course",
            "course_desc": "New Description",
            "cost": 150,
            "classroom_hours": 12,
            "lab_hours": 8,
            "internship_hours": 4,
            "practical_hours": 6,
            "location": "",  # Testing that it falls back to provider address
        }

        # Post the data
        response = self.client.post(reverse("new_course"), course_data)

        # Should redirect to manage_courses page
        self.assertRedirects(response, reverse("manage_courses"))

        # Check that the course was created
        self.assertTrue(Course.objects.filter(name="New Test Course").exists())

        # Get the created course
        new_course = Course.objects.get(name="New Test Course")

        # Check that the course has the provider's address as location
        self.assertEqual(new_course.location, self.provider.address)

        # Check that success message was shown
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "Course 'New Test Course' has been successfully posted."
        )

    def test_post_new_course_post_invalid(self):
        """Test POST request to post_new_course view with invalid data"""
        # Empty data to trigger form validation error
        course_data = {}

        # Post the data
        response = self.client.post(reverse("new_course"), course_data)

        # Should redirect to manage_courses page (even with form errors)
        self.assertRedirects(response, reverse("manage_courses"))

        # Check that error message was shown
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "Invalid data. Please check the form and try again."
        )

    @patch("logging.Logger.error")
    def test_post_new_course_exception(self, mock_logger):
        """Test exception handling in post_new_course view"""
        # Setup mock to raise exception during form.save
        with patch(
            "courses.forms.CourseForm.save", side_effect=Exception("Test error")
        ):
            course_data = {
                "name": "Exception Course",
                "course_desc": "This will cause an exception",
                "cost": 150,
                "classroom_hours": 12,
                "lab_hours": 8,
                "internship_hours": 4,
                "practical_hours": 6,
            }

            # We need to make the form valid but cause an exception during save
            with patch("courses.forms.CourseForm.is_valid", return_value=True):
                response = self.client.post(reverse("new_course"), course_data)

                # Should redirect to manage_courses page
                self.assertRedirects(response, reverse("manage_courses"))

                # Check that error message was shown
                messages = list(get_messages(response.wsgi_request))
                self.assertEqual(len(messages), 1)
                self.assertEqual(
                    str(messages[0]), "An error occurred while creating the course."
                )

                # Check that logger was called
                mock_logger.assert_called_once_with("Error creating course: Test error")

    def test_delete_course_authorized(self):
        """Test delete_course view when user is authorized"""
        # Make a POST request to delete
        response = self.client.post(
            reverse("delete_course", kwargs={"course_id": self.course1.course_id})
        )

        # Should redirect to course_list
        self.assertRedirects(response, reverse("manage_courses"))

        # Check that course was deleted
        self.assertFalse(Course.objects.filter(pk=self.course1.pk).exists())

    def test_delete_course_unauthorized(self):
        """Test delete_course view when user is not the provider of the course"""
        # Create another user and provider
        other_user = CustomUser.objects.create_user(
            username="otheruser", email="other@example.com", password="testpassword"
        )

        other_provider = Provider.objects.create(
            user=other_user, name="Other Provider", address="456 Other Street"
        )

        # Create a course for the other provider
        other_course = Course.objects.create(
            provider=other_provider,
            name="Other Course",
            course_desc="Other Description",
            cost=300,
            classroom_hours=20,
            lab_hours=10,
            internship_hours=5,
            practical_hours=5,
            location=other_provider.address,
        )

        # Try to delete the other provider's course
        response = self.client.post(
            reverse("delete_course", kwargs={"course_id": other_course.course_id})
        )

        # Should return forbidden
        self.assertEqual(response.status_code, 403)

        # Check that course still exists
        self.assertTrue(Course.objects.filter(pk=other_course.pk).exists())

    def test_edit_course_get(self):
        """Test GET request to edit_course view"""
        response = self.client.get(
            reverse("edit_course", kwargs={"course_id": self.course1.pk})
        )

        # Check that response is 200 OK
        self.assertEqual(response.status_code, 302)

        # Check that correct template is used
        self.assertRedirects(response, reverse("manage_courses"))

    def test_edit_course_post_authorized(self):
        """Test POST request to edit_course view when user is authorized"""
        # Data for updating the course
        updated_data = {
            "name": "Updated Course Name",
            "keywords": "updated, keywords",
            "course_desc": "Updated description",
            "cost": 150,
            "location": "Updated Location",
            "classroom_hours": 15,
            "lab_hours": 10,
            "internship_hours": 5,
            "practical_hours": 5,
        }

        # Post the data
        response = self.client.post(
            reverse("edit_course", kwargs={"course_id": self.course1.pk}), updated_data
        )

        # Should redirect to manage_courses
        self.assertRedirects(response, reverse("manage_courses"))

        # Refresh course from database
        self.course1.refresh_from_db()

        # Check that course was updated
        self.assertEqual(self.course1.name, "Updated Course Name")
        self.assertEqual(self.course1.keywords, "updated, keywords")
        self.assertEqual(self.course1.course_desc, "Updated description")
        self.assertEqual(self.course1.cost, 150)
        self.assertEqual(self.course1.location, "Updated Location")
        self.assertEqual(self.course1.classroom_hours, 15)
        self.assertEqual(self.course1.lab_hours, 10)
        self.assertEqual(self.course1.internship_hours, 5)
        self.assertEqual(self.course1.practical_hours, 5)

        # Check that success message was shown
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Edit course successfully!")

    def test_edit_course_unauthorized(self):
        """Test edit_course view when user is not the provider of the course"""
        # Create another user and provider
        other_user = CustomUser.objects.create_user(
            username="otheruser", email="other@example.com", password="testpassword"
        )

        other_provider = Provider.objects.create(
            user=other_user, name="Other Provider", address="456 Other Street"
        )

        # Create a course for the other provider
        other_course = Course.objects.create(
            provider=other_provider,
            name="Other Course",
            course_desc="Other Description",
            cost=300,
            classroom_hours=20,
            lab_hours=10,
            internship_hours=5,
            practical_hours=5,
            location=other_provider.address,
        )

        # Try to edit the other provider's course
        updated_data = {
            "name": "Should Not Update",
        }

        response = self.client.post(
            reverse("edit_course", kwargs={"course_id": other_course.pk}), updated_data
        )

        # Should return forbidden
        self.assertEqual(response.status_code, 403)

        # Check that course was not updated
        other_course.refresh_from_db()
        self.assertEqual(other_course.name, "Other Course")
