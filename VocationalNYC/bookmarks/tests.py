from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import BookmarkList, Bookmark, Course
from users.models import Provider

User = get_user_model()


class BookmarkListTests(TestCase):
    def setUp(self):
        # create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="password123")

        # create default bookmark list for the user
        self.default_list = BookmarkList.objects.create(user=self.user, name="default")
        # create a test provider
        self.provider = Provider.objects.create(
            name="Test Provider", phone_num="1234567890"
        )
        # create a test course
        self.course = Course.objects.create(
            name="Introduction to Computer Science",
            provider=self.provider,
        )

    def test_create_bookmark_list(self):
        """test creating a new bookmark list"""
        response = self.client.post(
            reverse("create_bookmark_list"), {"name": "My Favorites"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            BookmarkList.objects.filter(user=self.user, name="My Favorites").exists()
        )

        # test creating a list with the same name
        response = self.client.post(
            reverse("create_bookmark_list"), {"name": "My Favorites"}
        )
        self.assertEqual(response.status_code, 200)

        # test empty name
        response = self.client.post(reverse("create_bookmark_list"), {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a name for the list.")

    def test_delete_bookmark_list(self):
        """test deleting a bookmark list"""
        custom_list = BookmarkList.objects.create(user=self.user, name="Custom List")

        # test deleting default list
        response = self.client.post(
            reverse(
                "delete_bookmark_list", kwargs={"list_id": self.default_list.list_id}
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            BookmarkList.objects.filter(user=self.user, name="default").exists()
        )

        # test deleting custom list
        response = self.client.post(
            reverse("delete_bookmark_list", kwargs={"list_id": custom_list.list_id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            BookmarkList.objects.filter(list_id=custom_list.list_id).exists()
        )

    def test_add_bookmark(self):
        """test adding a bookmark to a list"""
        # GET request test
        response = self.client.get(
            reverse("add_bookmark", kwargs={"course_id": self.course.course_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.name)

        # POST request test - add bookmark to the default list
        response = self.client.post(
            reverse("add_bookmark", kwargs={"course_id": self.course.course_id}),
            {"bookmark_list": self.default_list.list_id},
        )
        self.assertEqual(response.status_code, 302)

        # verify that the bookmark was added
        self.assertTrue(
            Bookmark.objects.filter(
                bookmark_list=self.default_list, course=self.course
            ).exists()
        )

    def test_delete_bookmark(self):
        """test deleting a bookmark from a list"""
        # create a bookmark
        bookmark = Bookmark.objects.create(
            bookmark_list=self.default_list,
            course=self.course,
            time=timezone.now().date(),
        )

        # GET request test - should show the delete confirmation page
        response = self.client.get(
            reverse(
                "delete_bookmark",
                kwargs={
                    "list_id": self.default_list.list_id,
                    "bookmark_id": bookmark.id,
                },
            )
        )
        self.assertEqual(response.status_code, 200)

        # POST request test - confirm delete
        response = self.client.post(
            reverse(
                "delete_bookmark",
                kwargs={
                    "list_id": self.default_list.list_id,
                    "bookmark_id": bookmark.id,
                },
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Bookmark.objects.filter(id=bookmark.id).exists())

    def test_unauthorized_access(self):
        """test unauthorized access to bookmark lists"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="password123"
        )

        # create a bookmark list for the other user
        other_list = BookmarkList.objects.create(user=other_user, name="Other List")

        # test unauthorized access to the list detail
        response = self.client.get(
            reverse("bookmark_list_detail", kwargs={"list_id": other_list.list_id})
        )
        # should return 404
        self.assertEqual(response.status_code, 404)
