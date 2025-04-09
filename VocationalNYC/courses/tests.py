# import unittest
from unittest.mock import patch

# import json

from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse

from courses.views import CourseListView,sort_by
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


    @patch("your_module.filterCourses", side_effect=mock_filterCourses)
    def test_sort_by_function_default_order(self, mock_filter_courses):
        # Create a request without sorting parameters (default behavior)
        request = self.factory.get("/courses")

        # Call the sort_by function
        response = sort_by(request)

        # Verify the response is rendered correctly
        self.assertIsInstance(response, TemplateResponse)
        self.assertEqual(response.status_code, 200)

        # Check that courses are not sorted (default order)
        unsorted_courses = list(response.context_data["courses"])
        self.assertEqual(unsorted_courses[0].name, "Course A")
        self.assertEqual(unsorted_courses[1].name, "Course B")
        self.assertEqual(unsorted_courses[2].name, "Course C")

class FilterCoursesTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create test provider
        self.provider = Provider.objects.create(
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St, New York, NY, 10001"
        )
        
        # Create test courses with different attributes
        self.course1 = Course.objects.create(
            name="Python Course",
            provider=self.provider,
            keywords="python, programming",
            course_desc="Learn Python programming",
            cost=1000,
            location="123 Test St, New York, NY, 10001",
            classroom_hours=40,
            lab_hours=20
        )
        
        self.course2 = Course.objects.create(
            name="Web Development",
            provider=self.provider,
            keywords="web, javascript",
            course_desc="Learn web development",
            cost=2000,
            location="456 Test Ave, Brooklyn, NY, 11201",
            classroom_hours=60,
            lab_hours=30
        )

    def test_filter_by_keywords(self):
        request = self.factory.get('/search/', {'keywords': 'python'})
        context = filterCourses(request)
        self.assertEqual(len(context['courses']), 1)
        self.assertEqual(context['courses'][0].name, "Python Course")

    def test_filter_by_provider(self):
        request = self.factory.get('/search/', {'provider': 'Test Provider'})
        context = filterCourses(request)
        self.assertEqual(len(context['courses']), 2)

    def test_filter_by_cost_range(self):
        request = self.factory.get('/search/', {'min_cost': '1500', 'max_cost': '2500'})
        context = filterCourses(request)
        self.assertEqual(len(context['courses']), 1)
        self.assertEqual(context['courses'][0].name, "Web Development")

    def test_filter_by_location(self):
        request = self.factory.get('/search/', {'location': 'Brooklyn'})
        context = filterCourses(request)
        self.assertEqual(len(context['courses']), 1)
        self.assertEqual(context['courses'][0].name, "Web Development")

    def test_filter_by_classroom_hours(self):
        request = self.factory.get('/search/', {'min_classroom_hours': '50'})
        context = filterCourses(request)
        self.assertEqual(len(context['courses']), 1)
        self.assertEqual(context['courses'][0].name, "Web Development")

    def test_invalid_filters(self):
        request = self.factory.get('/search/', {
            'min_cost': 'invalid',
            'max_cost': 'invalid',
            'min_classroom_hours': 'invalid'
        })
        context = filterCourses(request)
        self.assertEqual(len(context['courses']), 2)  # Should return all courses

class CourseMapTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        
        # Create test provider and course
        self.provider = Provider.objects.create(
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St, New York, NY, 10001"
        )
        
        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            location="123 Test St, New York, NY, 10001"
        )

    def test_course_map_view(self):
        response = self.client.get(reverse('course_map'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/course_map.html')

    @patch('courses.views.requests.get')
    def test_course_data_view(self, mock_get):
        mock_get.return_value = MockResponse({
            'results': [{
                'geometry': {
                    'location': {
                        'lat': 40.7128,
                        'lng': -74.0060
                    }
                }
            }]
        })
        
        response = self.client.get(reverse('course_data'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            [{
                'name': 'Test Course',
                'location': '123 Test St, New York, NY, 10001',
                'lat': 40.7128,
                'lng': -74.0060
            }]
        )

class PostNewCourseTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        
        # Create test user and provider
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.provider = Provider.objects.create(
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St, New York, NY, 10001"
        )
        
        self.client.login(username='testuser', password='testpass123')

    def test_post_new_course_get(self):
        response = self.client.get(reverse('post_new_course'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/post_new_course.html')

    def test_post_new_course_post_valid(self):
        data = {
            'name': 'New Test Course',
            'provider': self.provider.id,
            'course_desc': 'Test course description',
            'cost': 1000,
            'location': '123 Test St, New York, NY, 10001',
            'classroom_hours': 40,
            'lab_hours': 20,
            'keywords': 'test, course'
        }
        
        response = self.client.post(reverse('post_new_course'), data)
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertTrue(Course.objects.filter(name='New Test Course').exists())

    def test_post_new_course_post_invalid(self):
        data = {
            'name': '',  # Invalid: empty name
            'provider': self.provider.id,
            'course_desc': 'Test course description',
            'cost': -100,  # Invalid: negative cost
            'location': '123 Test St, New York, NY, 10001',
            'classroom_hours': -40,  # Invalid: negative hours
            'lab_hours': 20
        }
        
        response = self.client.post(reverse('post_new_course'), data)
        self.assertEqual(response.status_code, 200)  # Should stay on form page
        self.assertFalse(Course.objects.filter(course_desc='Test course description').exists())

class CourseListViewBookmarksTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        
        # Create test user
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test provider and course
        self.provider = Provider.objects.create(
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St, New York, NY, 10001"
        )
        
        self.course = Course.objects.create(
            name="Test Course",
            provider=self.provider,
            location="123 Test St, New York, NY, 10001"
        )
        
        self.client.login(username='testuser', password='testpass123')

    def test_context_with_bookmarks(self):
        # Create a bookmark list
        from bookmarks.models import BookmarkList
        bookmark_list = BookmarkList.objects.create(
            user=self.user,
            name="My Bookmarks"
        )
        
        response = self.client.get(reverse('course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('bookmark_lists', response.context)
        self.assertIn('default_bookmark_list', response.context)
        self.assertEqual(response.context['default_bookmark_list'], bookmark_list)

    def test_context_without_bookmarks(self):
        response = self.client.get(reverse('course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['bookmark_lists']), [])
        self.assertIsNone(response.context['default_bookmark_list'])

class SortByTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create test provider
        self.provider = Provider.objects.create(
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St, New York, NY, 10001"
        )
        
        # Create test courses with different attributes for sorting
        self.course1 = Course.objects.create(
            name="Python Course",
            provider=self.provider,
            cost=1000,
            classroom_hours=40,
            location="123 Test St, New York, NY, 10001"
        )
        
        self.course2 = Course.objects.create(
            name="Web Development",
            provider=self.provider,
            cost=2000,
            classroom_hours=60,
            location="456 Test Ave, Brooklyn, NY, 11201"
        )
        
        self.course3 = Course.objects.create(
            name="Data Science",
            provider=self.provider,
            cost=1500,
            classroom_hours=50,
            location="789 Test Blvd, Queens, NY, 11301"
        )

    def test_sort_by_name_ascending(self):
        request = self.factory.get('/courses/sort/', {'sort': 'name', 'order': 'asc'})
        response = sort_by(request)
        
        self.assertEqual(response.status_code, 200)
        courses = list(response.context['courses'])
        self.assertEqual(courses[0].name, "Data Science")
        self.assertEqual(courses[1].name, "Python Course")
        self.assertEqual(courses[2].name, "Web Development")

    def test_sort_by_name_descending(self):
        request = self.factory.get('/courses/sort/', {'sort': 'name', 'order': 'desc'})
        response = sort_by(request)
        
        self.assertEqual(response.status_code, 200)
        courses = list(response.context['courses'])
        self.assertEqual(courses[0].name, "Web Development")
        self.assertEqual(courses[1].name, "Python Course")
        self.assertEqual(courses[2].name, "Data Science")

    def test_sort_by_cost_ascending(self):
        request = self.factory.get('/courses/sort/', {'sort': 'cost', 'order': 'asc'})
        response = sort_by(request)
        
        self.assertEqual(response.status_code, 200)
        courses = list(response.context['courses'])
        self.assertEqual(courses[0].cost, 1000)
        self.assertEqual(courses[1].cost, 1500)
        self.assertEqual(courses[2].cost, 2000)

    def test_sort_by_cost_descending(self):
        request = self.factory.get('/courses/sort/', {'sort': 'cost', 'order': 'desc'})
        response = sort_by(request)
        
        self.assertEqual(response.status_code, 200)
        courses = list(response.context['courses'])
        self.assertEqual(courses[0].cost, 2000)
        self.assertEqual(courses[1].cost, 1500)
        self.assertEqual(courses[2].cost, 1000)

    def test_sort_by_classroom_hours_ascending(self):
        request = self.factory.get('/courses/sort/', {'sort': 'classroom_hours', 'order': 'asc'})
        response = sort_by(request)
        
        self.assertEqual(response.status_code, 200)
        courses = list(response.context['courses'])
        self.assertEqual(courses[0].classroom_hours, 40)
        self.assertEqual(courses[1].classroom_hours, 50)
        self.assertEqual(courses[2].classroom_hours, 60)

    def test_sort_by_classroom_hours_descending(self):
        request = self.factory.get('/courses/sort/', {'sort': 'classroom_hours', 'order': 'desc'})
        response = sort_by(request)
        
        self.assertEqual(response.status_code, 200)
        courses = list(response.context['courses'])
        self.assertEqual(courses[0].classroom_hours, 60)
        self.assertEqual(courses[1].classroom_hours, 50)
        self.assertEqual(courses[2].classroom_hours, 40)

    def test_default_sort(self):
        request = self.factory.get('/courses/sort/')
        response = sort_by(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['courses']), 3)

    def test_invalid_sort_field(self):
        request = self.factory.get('/courses/sort/', {'sort': 'invalid_field', 'order': 'asc'})
        response = sort_by(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['courses']), 3)

    def test_invalid_order(self):
        request = self.factory.get('/courses/sort/', {'sort': 'name', 'order': 'invalid'})
        response = sort_by(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['courses']), 3)