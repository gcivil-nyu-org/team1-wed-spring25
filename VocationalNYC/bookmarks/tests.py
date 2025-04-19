from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.messages import get_messages
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
        self.custom_list = BookmarkList.objects.create(
            user=self.user, name="My Courses"
        )

        # create a test provider
        self.provider = Provider.objects.create(
            name="Test Provider", phone_num="1234567890"
        )
        # create a test course
        self.course1 = Course.objects.create(
            name="Introduction to Computer Science",
            provider=self.provider,
        )
        self.course2 = Course.objects.create(
            name="Advanced Python Programming",
            provider=self.provider,
        )
        self.course3 = Course.objects.create(
            name="Web Development",
            provider=self.provider,
        )

        Bookmark.objects.create(
            bookmark_list=self.default_list,
            course=self.course1,
            time=timezone.now().date(),
        )
        Bookmark.objects.create(
            bookmark_list=self.custom_list,
            course=self.course2,
            time=timezone.now().date(),
        )

        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="other123"
        )
        self.other_list = BookmarkList.objects.create(
            user=self.other_user, name="Other List"
        )

    def test_bookmark_list_view(self):
        response = self.client.get(reverse("bookmark_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookmarks/bookmark_list.html")

        self.assertIn("lists", response.context)
        self.assertEqual(len(response.context["lists"]), 2)

        list_ids = [lst.list_id for lst in response.context["lists"]]
        self.assertIn(self.default_list.list_id, list_ids)
        self.assertIn(self.custom_list.list_id, list_ids)
        self.assertNotIn(self.other_list.list_id, list_ids)

    def test_bookmark_list_detail_view(self):
        response = self.client.get(
            reverse(
                "bookmark_list_detail", kwargs={"list_id": self.default_list.list_id}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookmarks/bookmark_list_detail.html")

        self.assertIn("bookmark_list", response.context)
        self.assertEqual(response.context["bookmark_list"], self.default_list)

        response = self.client.get(
            reverse("bookmark_list_detail", kwargs={"list_id": self.other_list.list_id})
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_access(self):
        # test unauthorized access to the list detail

        response = self.client.get(
            reverse("bookmark_list_detail", kwargs={"list_id": self.other_list.list_id})
        )
        # should return 404
        self.assertEqual(response.status_code, 404)

        self.client.logout()

        response = self.client.get(reverse("bookmark_list"))
        self.assertRedirects(
            response, f"{reverse('account_login')}?next={reverse('bookmark_list')}"
        )

        response = self.client.get(
            reverse(
                "bookmark_list_detail", kwargs={"list_id": self.default_list.list_id}
            )
        )

        self.assertRedirects(
            response,
            f"{'/login/'}?next={reverse('bookmark_list_detail', kwargs={'list_id': self.default_list.list_id})}",
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
            reverse("add_bookmark", kwargs={"course_id": self.course1.course_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course1.name)

        # POST request test - add bookmark to the default list
        response = self.client.post(
            reverse("add_bookmark", kwargs={"course_id": self.course1.course_id}),
            {"bookmark_list": self.default_list.list_id},
        )
        self.assertEqual(response.status_code, 200)

        # verify that the bookmark was added
        self.assertTrue(
            Bookmark.objects.filter(
                bookmark_list=self.default_list, course=self.course1
            ).exists()
        )

    def test_add_bookmark_duplicate(self):
        Bookmark.objects.create(
            bookmark_list=self.default_list,
            course=self.course3,
            time=timezone.now().date(),
        )

        response = self.client.post(
            reverse("add_bookmark", kwargs={"course_id": self.course3.course_id}),
            {"bookmark_list": self.default_list.list_id},
        )

        self.assertEqual(response.status_code, 200)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]), "This course is already in the bookmark list."
        )

        self.assertEqual(
            Bookmark.objects.filter(
                bookmark_list=self.default_list, course=self.course1
            ).count(),
            1,
        )

    def test_delete_bookmark(self):
        """test deleting a bookmark from a list"""
        # create a bookmark
        bookmark = Bookmark.objects.create(
            bookmark_list=self.default_list,
            course=self.course3,
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
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Bookmark.objects.filter(id=bookmark.id).exists())

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


class RenameBookmarkListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="password123")

        self.default_list = BookmarkList.objects.create(user=self.user, name="default")
        self.custom_list = BookmarkList.objects.create(
            user=self.user, name="My Courses"
        )
        self.another_list = BookmarkList.objects.create(
            user=self.user, name="Another List"
        )

    def test_rename_bookmark_list_success(self):
        response = self.client.post(
            reverse(
                "rename_bookmark_list", kwargs={"list_id": self.custom_list.list_id}
            ),
            {"name": "Renamed List"},
        )

        self.assertRedirects(response, reverse("bookmark_list"))

        self.custom_list.refresh_from_db()
        self.assertEqual(self.custom_list.name, "Renamed List")

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Bookmark list renamed successfully.")

    def test_rename_bookmark_list_empty_name(self):
        response = self.client.post(
            reverse(
                "rename_bookmark_list", kwargs={"list_id": self.custom_list.list_id}
            ),
            {"name": "  "},
        )

        self.assertRedirects(response, reverse("bookmark_list"))

        self.custom_list.refresh_from_db()
        self.assertEqual(self.custom_list.name, "My Courses")

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Please enter a new name.")

    def test_rename_bookmark_list_duplicate_name(self):
        response = self.client.post(
            reverse(
                "rename_bookmark_list", kwargs={"list_id": self.custom_list.list_id}
            ),
            {"name": "Another List"},
        )

        self.assertRedirects(response, reverse("bookmark_list"))

        self.custom_list.refresh_from_db()
        self.assertEqual(self.custom_list.name, "My Courses")

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]), "A bookmark list with this name already exists."
        )

    def test_rename_bookmark_list_case_insensitive(self):
        response = self.client.post(
            reverse(
                "rename_bookmark_list", kwargs={"list_id": self.custom_list.list_id}
            ),
            {"name": "another list"},
        )

        self.assertRedirects(response, reverse("bookmark_list"))

        self.custom_list.refresh_from_db()
        self.assertEqual(self.custom_list.name, "My Courses")

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]), "A bookmark list with this name already exists."
        )

    def test_rename_nonexistent_list(self):
        # use unexisting list_id
        response = self.client.post(
            reverse("rename_bookmark_list", kwargs={"list_id": 9999}),
            {"name": "New Name"},
        )

        self.assertEqual(response.status_code, 404)
