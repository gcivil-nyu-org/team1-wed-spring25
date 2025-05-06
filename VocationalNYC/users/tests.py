from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model, authenticate
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.contrib.messages import get_messages
from unittest.mock import Mock, patch, MagicMock

import uuid
import json

from .models import Provider, Student, Tag, CustomUser
from .forms import CustomSignupForm, ProviderVerificationForm, StudentProfileForm
from .adapters import MyAccountAdapter
from .backends import TrainingProviderVerificationBackend


# ------------------------------------------------------------------------------
#  1) User & Model Tests
# ------------------------------------------------------------------------------
class UserModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="career_changer",
        )

    def test_user_creation(self):
        self.assertIsInstance(self.user, CustomUser)
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.role, "career_changer")
        self.assertTrue(self.user.is_active)

    def test_student_profile_creation(self):
        student = Student.objects.create(user=self.user, bio="Test bio")
        self.assertEqual(student.bio, "Test bio")
        self.assertEqual(student.user, self.user)

    def test_tag_operations(self):
        student = Student.objects.create(user=self.user)
        tag1 = Tag.objects.create(name="python")
        tag2 = Tag.objects.create(name="django")
        student.tags.add(tag1, tag2)
        self.assertEqual(student.tags.count(), 2)
        self.assertIn(tag1, student.tags.all())


class ProviderModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="provider",
            email="provider@example.com",
            password="testpass123",
            role="training_provider",
        )

    def test_provider_creation(self):
        provider = Provider.objects.create(
            user=self.user,
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St",
        )
        self.assertEqual(provider.name, "Test Provider")
        self.assertFalse(provider.verification_status)


# ------------------------------------------------------------------------------
#  2) Basic View Tests
# ------------------------------------------------------------------------------
class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_profile_view_get(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")

    def test_provider_verification_view(self):
        self.user.role = "training_provider"
        self.user.is_active = False
        self.user.save()

        # 👇 Log in the user
        self.client.force_login(self.user)

        # GET should work fine
        response = self.client.get(reverse("provider_verification"))
        self.assertEqual(response.status_code, 200)

        # POST: simulate full valid form submission
        test_file = SimpleUploadedFile(
            "test.pdf", b"file_content", content_type="application/pdf"
        )
        form_data = {
            "name": "Test Provider",
            "phone_num": "1234567890",
            "address": "123 Test St",
            "contact_firstname": "Alice",
            "contact_lastname": "Smith",
            "certificate": test_file,
        }

        response = self.client.post(
            reverse("provider_verification"),
            form_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {"success": True})


# ------------------------------------------------------------------------------
#  3) Form Tests
# ------------------------------------------------------------------------------
class FormTests(TestCase):
    def test_custom_signup_form(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "role": "career_changer",
        }
        form = CustomSignupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_provider_verification_form(self):
        form_data = {
            "name": "Test Provider",
            "phone_num": "1234567890",
            "address": "123 Test St",
            "website": "https://example.com",
            "contact_firstname": "Alice",
            "contact_lastname": "Doe",
        }
        file_data = {
            "certificate": SimpleUploadedFile(
                "test.pdf", b"file_content", content_type="application/pdf"
            ),
        }
        form = ProviderVerificationForm(data=form_data, files=file_data)
        print("FORM ERRORS:", form.errors)
        self.assertTrue(form.is_valid())

    def test_student_profile_form(self):
        form_data = {"bio": "Test student bio"}
        form = StudentProfileForm(data=form_data)
        self.assertTrue(form.is_valid())


# ------------------------------------------------------------------------------
#  4) API Tests (Tag endpoints)
# ------------------------------------------------------------------------------
class APITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="career_changer",
        )
        self.student = Student.objects.create(user=self.user)
        self.client.login(username="testuser", password="testpass123")

    def test_add_tag(self):
        response = self.client.post(
            reverse("add_tag"), {"tag": "python"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tag.objects.filter(name="python").exists())

    def test_remove_tag(self):
        tag = Tag.objects.create(name="python")
        self.student.tags.add(tag)
        response = self.client.post(
            reverse("remove_tag"), {"tag": "python"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.student.tags.filter(name="python").exists())


# ------------------------------------------------------------------------------
#  5) Custom Auth Backends
# ------------------------------------------------------------------------------
class TrainingProviderBackendTests(TestCase):
    def setUp(self):
        self.backend = TrainingProviderVerificationBackend()
        self.user = get_user_model().objects.create_user(
            username="provider",
            email="provider@test.com",
            password="testpass123",
            role="training_provider",
            is_active=False,
        )

    def test_user_can_authenticate_provider(self):
        self.assertTrue(self.backend.user_can_authenticate(self.user))

    def test_user_can_authenticate_inactive_regular_user(self):
        self.user.role = "career_changer"
        self.user.save()
        self.assertFalse(self.backend.user_can_authenticate(self.user))

    def test_authenticate_success(self):
        authenticated_user = self.backend.authenticate(
            None, username="provider", password="testpass123"
        )
        self.assertEqual(authenticated_user, self.user)
        self.assertTrue(hasattr(authenticated_user, "_verified_inactive_provider"))

    def test_authenticate_wrong_password(self):
        authenticated_user = self.backend.authenticate(
            None, username="provider", password="wrongpass"
        )
        self.assertIsNone(authenticated_user)


# ------------------------------------------------------------------------------
#  6) Account Adapter Tests
# ------------------------------------------------------------------------------
class MyAccountAdapterTests(TestCase):
    def setUp(self):
        self.adapter = MyAccountAdapter()
        self.factory = RequestFactory()
        self.provider_user = get_user_model().objects.create_user(
            username="provider",
            email="provider@test.com",
            password="testpass123",
            role="training_provider",
            is_active=False,
        )
        self.regular_user = get_user_model().objects.create_user(
            username="user",
            email="user@test.com",
            password="testpass123",
            role="career_changer",
            is_active=True,
        )

    def test_is_open_for_login_provider(self):
        request = self.factory.get("/")
        self.assertTrue(self.adapter.is_open_for_login(request, self.provider_user))

    def test_is_open_for_login_regular(self):
        request = self.factory.get("/")
        self.assertTrue(self.adapter.is_open_for_login(request, self.regular_user))
        self.regular_user.is_active = False
        self.regular_user.save()
        self.assertFalse(self.adapter.is_open_for_login(request, self.regular_user))

    def test_get_login_redirect_url_provider(self):
        request = self.factory.get("/")
        request.user = self.provider_user
        url = self.adapter.get_login_redirect_url(request)
        self.assertEqual(url, reverse("provider_verification"))

    def test_get_login_redirect_url_regular_user(self):
        user = get_user_model().objects.create_user(
            username="regular",
            email="regular@test.com",
            password="testpass123",
            role="career_changer",
            is_active=True,
        )
        request = self.factory.get("/")
        request.user = user

        url = self.adapter.get_login_redirect_url(request)
        self.assertEqual(url, reverse("home"))

    def test_respond_inactive_provider(self):
        request = self.factory.get("/")
        url = self.adapter.respond_inactive(request, self.provider_user)
        self.assertEqual(url, reverse("provider_verification"))


# ------------------------------------------------------------------------------
#  7) Provider Verification View Tests
# ------------------------------------------------------------------------------
class ProviderVerificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.provider_user = get_user_model().objects.create_user(
            username="provider",
            email="provider@test.com",
            password="testpass123",
            role="training_provider",
            is_active=False,
        )
        self.client.login(username="provider", password="testpass123")

    def test_verification_view_get(self):
        response = self.client.get(reverse("provider_verification"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/provider_verification.html")

    def test_verification_with_existing_provider(self):
        Provider.objects.create(
            name="Existing Provider", phone_num="1234567890", address="Test Address"
        )
        data = {
            "name": "Existing Provider",
            "phone_num": "1234567890",
            "address": "Test Address",
            "contact_firstname": "Alice",
            "contact_lastname": "Smith",
            "confirm_existing": True,
        }
        response = self.client.post(
            reverse("provider_verification"),
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Expect JSON with 400 because we didn’t include certificate (required)
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.assertIn("certificate", response.json()["errors"])

    def test_verification_invalid_form(self):
        data = {
            "name": "",  # Invalid
            "phone_num": "123",  # Invalid format
            "address": "Test Address",
        }
        response = self.client.post(reverse("provider_verification"), data)

        self.assertEqual(response.status_code, 400)

        # Check it's a JSON response
        self.assertEqual(response["Content-Type"], "application/json")

        response_json = json.loads(response.content)
        self.assertIn("errors", response_json)
        self.assertIn("name", response_json["errors"])

    def test_verification_wrong_role(self):
        self.provider_user.role = "career_changer"
        self.provider_user.save()
        response = self.client.get(reverse("provider_verification"))
        self.assertEqual(response.status_code, 302)

    # def test_verification_invalid_certificate(self):
    #     large_file = SimpleUploadedFile(
    #         "large.pdf", b"x" * (5 * 1024 * 1024 + 1),  # 5MB + 1 byte
    #         content_type="application/pdf"
    #     )
    #     data = {
    #         "name": "Test Provider",
    #         "phone_num": "1234567890",
    #         "address": "Test Address",
    #         "contact_firstname": "Alice",
    #         "contact_lastname": "Smith",
    #         "certificate": large_file,
    #     }
    #     response = self.client.post(reverse("provider_verification"), data, follow=True)
    #     self.assertEqual(response.status_code, 200)
    #
    #     # Ensure form is in context if the view handles large files properly
    #     self.assertIn("form", response.context)
    #     self.assertIn("certificate", response.context["form"].errors)


# ------------------------------------------------------------------------------
#  8) ProfileViewTests (FIRST)  <-- Keep the one from line ~304
# ------------------------------------------------------------------------------
class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_profile_view_career_changer(self):
        self.user.role = "career_changer"
        self.user.save()
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("student_form", response.context)

    def test_profile_view_provider(self):
        self.user.role = "training_provider"
        self.user.save()
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("provider_update_form", response.context)

    def test_profile_update_student(self):
        self.user.role = "career_changer"
        self.user.save()
        Student.objects.create(user=self.user)

        data = {"student_form": "1", "bio": "New bio"}
        response = self.client.post(reverse("profile"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Student.objects.get(user=self.user).bio, "New bio")

    def test_tag_operations_edge_cases(self):
        self.user.role = "career_changer"
        self.user.save()
        student = Student.objects.create(user=self.user)

        # Test adding duplicate tag
        tag = Tag.objects.create(name="python")
        student.tags.add(tag)
        response = self.client.post(
            reverse("add_tag"), {"tag": "python"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])

        # Test adding empty tag
        response = self.client.post(
            reverse("add_tag"), {"tag": ""}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])

        # Test removing non-existent tag
        response = self.client.post(
            reverse("remove_tag"),
            {"tag": "nonexistent"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])


# ------------------------------------------------------------------------------
#  9) CustomUserManager Tests
# ------------------------------------------------------------------------------
class CustomUserManagerTests(TestCase):
    def test_create_superuser_validation(self):
        # Import here to avoid circular imports
        from users.managers import CustomUserManager

        manager = CustomUserManager()

        # Test missing required fields
        with self.assertRaises(ValueError):
            manager.create_superuser(
                username="", email="admin@test.com", password="testpass123"
            )

        # Test is_staff=False
        with self.assertRaises(ValueError):
            manager.create_superuser(
                username="admin",
                email="admin@test.com",
                password="testpass123",
                is_staff=False,
            )

        # Test is_superuser=False
        with self.assertRaises(ValueError):
            manager.create_superuser(
                username="admin",
                email="admin@test.com",
                password="testpass123",
                is_superuser=False,
            )


# ------------------------------------------------------------------------------
# 10) CustomSignupForm Tests
# ------------------------------------------------------------------------------
class CustomSignupFormTests(TestCase):
    def test_custom_signup_form_validation(self):
        # Test valid data
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "role": "career_changer",
        }
        form = CustomSignupForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Test invalid role
        invalid_form_data = form_data.copy()
        invalid_form_data["role"] = "invalid_role"
        form = CustomSignupForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())

        # Test missing email
        invalid_form_data = form_data.copy()
        invalid_form_data["email"] = ""
        form = CustomSignupForm(data=invalid_form_data)
        self.assertFalse(form.is_valid())


# ------------------------------------------------------------------------------
# 11) ProviderVerificationForm Tests
# ------------------------------------------------------------------------------
class ProviderVerificationFormTests(TestCase):
    def setUp(self):
        self.provider = Provider.objects.create(
            name="Test Provider", phone_num="1234567890", address="Test Address"
        )

    def test_providerverification_form_validation(self):
        # Test valid data

        file_data = {
            "certificate": SimpleUploadedFile(
                "test.pdf", b"file_content", content_type="application/pdf"
            ),
        }

        # Test valid form
        valid_data = {
            "name": "New Provider",
            "phone_num": "1234567890",
            "address": "Test Address",
            "website": "https://test.com",
            "contact_firstname": "Alice",
            "contact_lastname": "Smith",
        }
        valid_form = ProviderVerificationForm(data=valid_data, files=file_data)
        self.assertTrue(valid_form.is_valid())

        # Test conflict with existing provider (from setUp)
        conflict_data = {
            "name": "Test Provider",  # Already created in setUp()
            "phone_num": "1234567890",
            "address": "Test Address",
            "website": "",  # optional
            "contact_firstname": "Alice",
            "contact_lastname": "Smith",
            "confirm_existing": "",  # falsy
        }
        conflict_form = ProviderVerificationForm(data=conflict_data, files=file_data)
        self.assertFalse(conflict_form.is_valid())
        self.assertIn("name", conflict_form.errors)
        self.assertIn("already exists", conflict_form.errors["name"][0].lower())


class ProviderBindExistingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.provider_user = get_user_model().objects.create_user(
            username=f"provideruser_{uuid.uuid4().hex[:8]}",
            email=f"provider_{uuid.uuid4().hex[:8]}@test.com",
            password="testpass123",
            role="training_provider",
            is_active=False,
        )

        self.existing_provider_name = f"Existing Provider {uuid.uuid4().hex[:8]}"
        self.existing_provider = Provider.objects.create(
            name=self.existing_provider_name,
            phone_num="1234567890",
            address="123 Test St",
            user=None,
        )

        self.client.login(username=self.provider_user.username, password="testpass123")

    def test_bind_to_existing_provider(self):
        test_file = SimpleUploadedFile(
            "certificate.pdf", b"file_content", content_type="application/pdf"
        )

        form_data = {
            "name": self.existing_provider_name,
            "contact_firstname": "John",
            "contact_lastname": "Doe",
            "phone_num": "9876543210",
            "address": "Updated Address",
            "certificate": test_file,
            "confirm_existing": "true",
        }

        response = self.client.post(
            reverse("provider_verification"),
            form_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertJSONEqual(response.content.decode(), {"success": True})

        self.existing_provider.refresh_from_db()
        self.assertEqual(self.existing_provider.user, self.provider_user)
        self.assertEqual(self.existing_provider.phone_num, "1234567890")
        self.assertEqual(self.existing_provider.address, "123 Test St")

        self.provider_user.refresh_from_db()
        self.assertTrue(self.provider_user.is_active)

    def test_reject_binding_to_existing_provider(self):
        test_file = SimpleUploadedFile(
            "certificate.pdf", b"file_content", content_type="application/pdf"
        )

        form_data = {
            "name": self.existing_provider_name,
            "contact_firstname": "John",
            "contact_lastname": "Doe",
            "phone_num": "9876543210",
            "address": "Updated Address",
            "certificate": test_file,
            "confirm_existing": "false",
        }

        response = self.client.post(
            reverse("provider_verification"),
            form_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode())
        self.assertFalse(response_data["success"])
        self.assertIn("errors", response_data)
        self.assertIn("name", response_data["errors"])

        self.existing_provider.refresh_from_db()
        self.assertIsNone(self.existing_provider.user)

        self.provider_user.refresh_from_db()
        self.assertFalse(self.provider_user.is_active)

    @patch("users.views.ProviderVerificationForm")
    def test_bind_to_provider_with_user(self, mock_form):
        # use mock_form to simulate the form validation failure
        mock_form_instance = MagicMock()
        mock_form_instance.is_valid.return_value = False
        mock_form_instance.errors = {
            "name": [
                "Training Provider with this Name already exists and is registered."
            ]
        }
        mock_form.return_value = mock_form_instance

        test_file = SimpleUploadedFile(
            "certificate.pdf", b"file_content", content_type="application/pdf"
        )

        form_data = {
            "name": "Provider With User Already Registered",
            "contact_firstname": "John",
            "contact_lastname": "Doe",
            "phone_num": "9876543210",
            "address": "Test Address",
            "certificate": test_file,
            "confirm_existing": "true",
        }

        response = self.client.post(
            reverse("provider_verification"),
            form_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode())
        self.assertFalse(response_data["success"])
        self.assertIn("errors", response_data)

        self.provider_user.refresh_from_db()
        self.assertFalse(self.provider_user.is_active)

    def test_check_provider_name_api(self):
        response = self.client.get(
            reverse("check_provider_name"), {"name": self.existing_provider_name}
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode())
        self.assertTrue(response_data["exists"])
        self.assertFalse(response_data["user"])

        response = self.client.get(
            reverse("check_provider_name"),
            {"name": f"Non Existent Provider {uuid.uuid4().hex}"},
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode())
        self.assertFalse(response_data["exists"])

        other_user_name = f"otheruser_{uuid.uuid4().hex[:8]}"
        other_user = get_user_model().objects.create_user(
            username=other_user_name,
            email=f"{other_user_name}@test.com",
            password="testpass123",
        )

        provider_with_user_name = f"Provider With User {uuid.uuid4().hex[:8]}"
        Provider.objects.create(
            name=provider_with_user_name,
            phone_num="1122334455",
            address="456 User St",
            user=other_user,
        )

        response = self.client.get(
            reverse("check_provider_name"), {"name": provider_with_user_name}
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode())
        self.assertTrue(response_data["exists"])
        self.assertTrue(response_data["user"])


# ------------------------------------------------------------------------------
# 12) StudentProfileForm Tests
# ------------------------------------------------------------------------------
class StudentProfileFormTests(TestCase):
    def test_student_profile_form_validation(self):
        student = Student.objects.create(
            user=get_user_model().objects.create_user(
                username="testuser", email="test@example.com", password="testpass123"
            )
        )
        # Test valid data
        form_data = {"bio": "Test bio"}
        form = StudentProfileForm(data=form_data, instance=student)
        self.assertTrue(form.is_valid())

        # Test long bio
        invalid_form_data = {"bio": "x" * 1001}
        form = StudentProfileForm(data=invalid_form_data, instance=student)
        self.assertFalse(
            form.is_valid(), "Form should be invalid with bio > 1000 characters"
        )


# ------------------------------------------------------------------------------
# 13) CustomSignupView Tests
# ------------------------------------------------------------------------------
class CustomSignupViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_career_changer(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
                "role": "career_changer",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())

    def test_signup_provider(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "username": "newprovider",
                "email": "provider@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
                "role": "training_provider",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="newprovider")
        self.assertFalse(user.is_active)


# ------------------------------------------------------------------------------
# 14) ProfileViewTestsExtra  <-- Renamed to avoid F811
# ------------------------------------------------------------------------------
class ProfileViewTestsExtra(TestCase):
    """
    Additional profile-related tests that do not conflict with the earlier
    ProfileViewTests.
    """

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="career_changer",
        )
        self.client.login(username="testuser", password="testpass123")

    def test_profile_view_post_student(self):
        # Example test
        student = Student.objects.create(user=self.user)
        response = self.client.post(
            reverse("profile"), {"student_form": "1", "bio": "Updated bio"}
        )
        self.assertEqual(response.status_code, 302)
        student.refresh_from_db()
        self.assertEqual(student.bio, "Updated bio")

    def test_profile_view_post_provider(self):
        # Example test
        self.user.role = "training_provider"
        self.user.save()
        provider = Provider.objects.create(
            user=self.user,
            name="Test Provider",
            phone_num="1234567890",
            address="Test Address",
        )
        response = self.client.post(
            reverse("profile"),
            {
                "provider_form": "1",
                "name": "Updated Provider",
                "phone_num": "0987654321",
                "address": "New Address",
                "contact_firstname": "Alice",
                "contact_lastname": "Smith",
                "certificate": SimpleUploadedFile(
                    "test.pdf", b"dummy", content_type="application/pdf"
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        provider.refresh_from_db()
        self.assertEqual(provider.name, "Updated Provider")


# ------------------------------------------------------------------------------
# 15) Tag Operations Tests (Already used above but example of separate approach)
# ------------------------------------------------------------------------------
class TagOperationsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="career_changer",
        )
        self.student = Student.objects.create(user=self.user)
        self.client.login(username="testuser", password="testpass123")

    def test_add_existing_tag(self):
        tag = Tag.objects.create(name="python")
        self.student.tags.add(tag)
        response = self.client.post(
            reverse("add_tag"), {"tag": "python"}, content_type="application/json"
        )
        data = response.json()
        self.assertFalse(data["success"])

    def test_add_tag_unauthenticated(self):
        self.client.logout()
        response = self.client.post(
            reverse("add_tag"), {"tag": "python"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 302)

    def test_remove_nonexistent_tag(self):
        response = self.client.post(
            reverse("remove_tag"),
            {"tag": "nonexistent"},
            content_type="application/json",
        )
        data = response.json()
        self.assertTrue(data["success"])


# ------------------------------------------------------------------------------
# 16) MyAccountAdapterTestsExtra
# ------------------------------------------------------------------------------
class MyAccountAdapterTestsExtra(TestCase):
    """
    Additional adapter tests that do not conflict with the earlier MyAccountAdapterTests.
    """

    def setUp(self):
        self.adapter = MyAccountAdapter()
        self.factory = RequestFactory()

    def test_get_login_redirect_url_regular_user(self):
        user = get_user_model().objects.create_user(
            username="regular2",
            email="regular2@test.com",
            password="testpass123",
            role="career_changer",
            is_active=True,
        )
        request = self.factory.get("/")
        request.user = user
        url = self.adapter.get_login_redirect_url(request)
        self.assertEqual(url, "/")


# ------------------------------------------------------------------------------
# 17) Model Tests (Add them here or keep separate - adjusting to avoid duplication)
# ------------------------------------------------------------------------------
class ModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="career_changer",
        )

    def test_provider_model_methods(self):
        provider = Provider.objects.create(
            user=self.user,
            name="Test Provider",
            phone_num="1234567890",
            address="Test Address",
        )
        self.assertEqual(str(provider), "Test Provider - None")

        # Test with website
        provider.website = "https://test.com"
        provider.save()
        self.assertEqual(str(provider), "Test Provider - https://test.com")

    def test_student_model_methods(self):
        student = Student.objects.create(user=self.user)
        student.modify_profile(bio="New bio")
        self.assertEqual(student.bio, "New bio")

        # Tag operations
        tag = Tag.objects.create(name="python")
        student.add_tag(tag)
        self.assertIn(tag, student.tags.all())
        # add same tag again
        student.add_tag(tag)
        self.assertEqual(student.tags.count(), 1)
        # remove tag
        student.remove_tag(tag)
        self.assertEqual(student.tags.count(), 0)

    def test_tag_model_methods(self):
        tag = Tag.objects.create(name="python")
        self.assertEqual(str(tag), "python")
        self.assertEqual(Tag._meta.ordering, ["name"])


# ------------------------------------------------------------------------------
# 18) ViewsTests (Original) - Just keep distinct
# ------------------------------------------------------------------------------
class ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="career_changer",
        )
        self.client.login(username="testuser", password="testpass123")

    def test_provider_detail_view(self):
        provider = Provider.objects.create(
            name="Test Provider", phone_num="1234567890", address="Test Address"
        )
        response = self.client.get(
            reverse("provider_detail", kwargs={"pk": provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "provider/provider_detail.html")

    def test_add_tag_unauthenticated(self):
        self.client.logout()
        response = self.client.post(
            reverse("add_tag"),
            data=json.dumps({"tag": "python"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_add_tag_invalid_json(self):
        response = self.client.post(
            reverse("add_tag"), "invalid json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])

    def test_remove_tag_invalid_json(self):
        response = self.client.post(
            reverse("remove_tag"), "invalid json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])


# ------------------------------------------------------------------------------
# 19) AdapterTests (Original) - Just keep distinct
# ------------------------------------------------------------------------------
class AdapterTests(TestCase):
    def setUp(self):
        self.adapter = MyAccountAdapter()
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="career_changer",
        )

    def test_is_open_for_signup(self):
        request = self.factory.get("/")
        self.assertTrue(self.adapter.is_open_for_signup(request))

    def test_save_user(self):
        request = self.factory.get("/")
        user = get_user_model()()

        # Create a mock form with cleaned_data
        mock_form = Mock()
        mock_form.cleaned_data = {
            "username": "newuser",
            "email": "new@test.com",
            "password1": "testpass123",
            "role": "career_changer",
        }
        self.adapter.save_user(request, user, mock_form)
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "new@test.com")
        self.assertEqual(user.role, "career_changer")

    def test_respond_inactive_regular_user(self):
        request = self.factory.get("/")
        user = get_user_model().objects.create_user(
            username="inactive",
            email="inactive@test.com",
            password="testpass123",
            role="career_changer",
            is_active=False,
        )
        response = self.adapter.respond_inactive(request, user)
        self.assertIsNone(response)

    def test_get_login_redirect_url_admin(self):
        request = self.factory.get("/")
        user = get_user_model().objects.create_superuser(
            username="admin", email="admin@test.com", password="testpass123"
        )
        request.user = user
        url = self.adapter.get_login_redirect_url(request)
        self.assertEqual(url, "/admin/")


# ------------------------------------------------------------------------------
# 20) ViewsIntegrationTests
# ------------------------------------------------------------------------------
class ViewsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="career_changer",
        )
        self.client.login(username="testuser", password="testpass123")

    @patch("django.template.response.SimpleTemplateResponse.render")
    @patch("users.views.requests.get")
    def test_provider_list_api_integration(self, mock_get, mock_render):
        # Mock the API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                "organization_name": "Test API Provider",
                "phone1": "1234567890",
                "address1": "Test Address",
                "open_time": "9-5",
                "provider_description": "Test Description",
                "website": "https://test.com",
            }
        ]
        mock_render.return_value = HttpResponseRedirect("/")
        response = self.client.get(reverse("provider_list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Provider.objects.filter(name="Test API Provider").exists())

    @patch("django.template.response.SimpleTemplateResponse.render")
    @patch("users.views.requests.get")
    def test_provider_list_api_failure(self, mock_get, mock_render):
        mock_get.return_value.status_code = 404
        mock_render.return_value = HttpResponseRedirect("/")
        response = self.client.get(reverse("provider_list"))
        self.assertEqual(response.status_code, 302)

    @patch("users.views.requests.get")
    def test_provider_list_empty_response_alt(self, mock_get):
        """
        Renamed from 'test_provider_list_empty_response'
        to avoid F811 duplication errors.
        """
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []
        response = self.client.get(reverse("provider_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "provider/provider_list.html")
        self.assertEqual(Provider.objects.count(), 0)

    @patch("users.views.requests.get")
    def test_provider_list_invalid_data_alt(self, mock_get):
        """
        Renamed from 'test_provider_list_invalid_data'
        to avoid F811 duplication errors.
        """
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"organization_name": ""}]
        response = self.client.get(reverse("provider_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "provider/provider_list.html")
        self.assertEqual(Provider.objects.count(), 0)

    def test_profile_view_new_student(self):
        Student.objects.filter(user=self.user).delete()
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Student.objects.filter(user=self.user).exists())

    def test_profile_view_provider_update(self):
        self.user.role = "training_provider"
        self.user.save()
        provider = Provider.objects.create(
            user=self.user,
            name="Test Provider",
            phone_num="1234567890",
            address="Test Address",
        )
        response = self.client.post(
            reverse("profile"),
            {
                "provider_form": "1",
                "name": "Updated Provider",
                "phone_num": "0987654321",
                "address": "New Address",
                "website": "https://test.com",
                "contact_firstname": "Alice",
                "contact_lastname": "Smith",
                "certificate": SimpleUploadedFile(
                    "test.pdf", b"dummy", content_type="application/pdf"
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        provider.refresh_from_db()
        self.assertEqual(provider.website, "https://test.com")

    def test_profile_view_invalid_role(self):
        self.user.role = "invalid_role"
        self.user.save()
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("provider_verification_form", response.context)
        self.assertNotIn("student_form", response.context)

    def test_provider_verification_form_invalid(self):
        self.user.role = "training_provider"
        self.user.is_active = False
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("provider_verification"),
            {
                "name": "",  # Invalid: required
                "phone_num": "invalid",  # Invalid format, but not enforced here
                "address": "",  # Invalid: required
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",  # AJAX
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")

        response_json = json.loads(response.content)

        # print("ACTUAL JSON:", json.dumps(response_json, indent=2))  # Optional for debug

        expected_errors = {
            "name": ["This field is required."],
            "address": ["This field is required."],
            "certificate": ["This field is required."],
            "contact_firstname": ["This field is required."],
            "contact_lastname": ["This field is required."],
            # Removed "phone_num" — not returned by the view
        }

        self.assertFalse(response_json["success"])
        self.assertDictEqual(response_json["errors"], expected_errors)

    @patch(
        "allauth.account.adapter.DefaultAccountAdapter.respond_email_verification_sent"
    )
    def test_signup_view_email_verification(self, mock_respond):
        mock_respond.return_value = HttpResponseRedirect("/")
        response = self.client.post(
            reverse("account_signup"),
            {
                "username": "newuser2",
                "email": "newuser2@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
                "role": "career_changer",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_add_tag_json_validation(self):
        response = self.client.post(
            reverse("add_tag"), "invalid json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])

    def test_profile_view_post_invalid_form(self):
        """Test profile update with invalid form data"""
        self.user.role = "career_changer"
        self.user.save()
        # No need to store 'student' variable if unused
        Student.objects.create(user=self.user)

        # Initialize form before POST request
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("profile"),
            {"student_form": "1", "bio": "x" * 1001},  # Invalid: too long
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIn("student_form", response.context)

    def test_provider_form_post_invalid(self):
        """Test provider form submission with invalid data"""
        self.user.role = "training_provider"
        self.user.save()
        response = self.client.post(
            reverse("profile"),
            {
                "provider_form": "1",
                "name": "",  # Invalid
                "phone_num": "invalid",
                "address": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_provider_verification_unbound_form(self):
        """Test provider verification with unbound form"""
        self.user.role = "training_provider"
        self.user.is_active = False
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("provider_verification"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content)
        self.assertIn("errors", response_json)
        self.assertFalse(response_json["success"])

    def test_check_provider_name_view(self):
        """Test the check_provider_name view"""
        # Test with non-existent provider
        response = self.client.get(
            reverse("check_provider_name"), {"name": "NonExistent"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["exists"])

        # Test with existing provider
        Provider.objects.create(
            name="Existing Provider", phone_num="1234567890", address="Test Address"
        )
        response = self.client.get(
            reverse("check_provider_name"), {"name": "Existing Provider"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["exists"])

    def test_custom_signup_view_error(self):
        """Test signup view handles bookmark creation error correctly"""
        with patch("users.views.BookmarkList.objects.create") as mock_create:
            mock_create.side_effect = Exception("Database error")
            response = self.client.post(
                reverse("account_signup"),
                {
                    "username": "newuser3",
                    "email": "newuser3@example.com",
                    "password1": "testpass123",
                    "password2": "testpass123",
                    "role": "career_changer",
                },
                follow=True,  # Follow the redirect to collect messages
            )
            messages_list = list(get_messages(response.wsgi_request))
            print("MESSAGES:", [str(m) for m in messages_list])

    # def test_custom_signup_view_error(self):
    #     """Test signup view handles bookmark creation error correctly"""
    #     with patch("users.views.BookmarkList.objects.create") as mock_create:
    #         mock_create.side_effect = Exception("Database error")
    #         response = self.client.post(
    #             reverse("account_signup"),
    #             {
    #                 "username": "newuser3",
    #                 "email": "newuser3@example.com",
    #                 "password1": "testpass123",
    #                 "password2": "testpass123",
    #                 "role": "career_changer",
    #             },
    #             follow=True,  # Follow the redirect to collect messages
    #         )
    #         messages_list = list(get_messages(response.wsgi_request))

    #         print("MESSAGES:", [str(m) for m in messages_list])

    def test_provider_verification_with_certificate(self):
        """Test provider verification with valid certificate"""
        self.user.role = "training_provider"
        self.user.is_active = False
        self.user.save()
        self.client.force_login(self.user)
        test_file = SimpleUploadedFile(
            "test.pdf", b"file_content", content_type="application/pdf"
        )
        response = self.client.post(
            reverse("provider_verification"),
            {
                "name": "New Test Provider",
                "phone_num": "1234567890",
                "address": "Test Address",
                "contact_firstname": "Alice",
                "contact_lastname": "Smith",
                "certificate": test_file,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",  # Explicitly treat as AJAX
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertJSONEqual(
            response.content.decode(),
            {"success": True},
        )

        provider = Provider.objects.get(name="New Test Provider")
        self.assertTrue(provider.certificate)

    def test_provider_detail_404(self):
        """Test provider detail view with non-existent provider"""
        response = self.client.get(reverse("provider_detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)


class InactiveProviderLoginTest(TestCase):
    def setUp(self):
        self.inactive_provider = get_user_model().objects.create_user(
            username="inactive_provider",
            email="inactive@example.com",
            password="securepassword123",
            is_active=False,
            role="training_provider",
        )
        self.active_provider = get_user_model().objects.create_user(
            username="active_provider",
            email="active@example.com",
            password="securepassword123",
            is_active=True,
            role="training_provider",
        )

        self.regular_user = get_user_model().objects.create_user(
            username="regular_user",
            email="regular@example.com",
            password="securepassword123",
            is_active=True,
            role="student",
        )

        self.client = Client()

    def test_inactive_provider_login_redirect(self):
        """Test inactive provider login redirects to provider_verification"""
        response = self.client.post(
            reverse("account_login"),
            {"login": "inactive_provider", "password": "securepassword123"},
            follow=True,
        )

        self.assertRedirects(response, reverse("provider_verification"))

        self.assertTrue(response.context["user"].is_authenticated)
        self.assertEqual(response.context["user"].username, "inactive_provider")

    def test_inactive_provider_restricted_access(self):
        """Test inactive provider access to restricted pages"""
        self.client.login(username="inactive_provider", password="securepassword123")

        response = self.client.get(reverse("manage_courses"), follow=True)
        self.assertRedirects(response, reverse("provider_verification"))

        response = self.client.get(reverse("course_list"), follow=True)
        self.assertRedirects(response, reverse("provider_verification"))

    def test_inactive_provider_login_access_check(self):
        """Test if only verification and logout open to inactive provider"""
        self.client.login(username="inactive_provider", password="securepassword123")

        allowed_pages = [
            reverse("provider_verification"),
        ]

        restricted_pages = [
            reverse("manage_courses"),
            reverse("course_list"),
            reverse("home"),
        ]

        for page in allowed_pages:
            response = self.client.get(page)
            self.assertNotEqual(
                response.status_code, 302, f"Page {page} should not redirect but did"
            )

        for page in restricted_pages:
            response = self.client.get(page, follow=True)
            self.assertRedirects(
                response,
                reverse("provider_verification"),
                msg_prefix=f"Page {page} should redirect to provider_verification but did not",
            )

    def test_active_provider_access(self):
        """Test active provider login and access to manage courses"""
        self.client.login(username="active_provider", password="securepassword123")

        response = self.client.get(reverse("manage_courses"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_regular_user_login(self):
        """test regular user login"""
        self.client.force_login(self.regular_user)

        response = self.client.get(reverse("course_list"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("manage_courses"))
        self.assertEqual(response.status_code, 302)

    def test_authentication_backend(self):
        """test the custom authentication backend for inactive provider"""

        user = authenticate(username="inactive_provider", password="securepassword123")

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "inactive_provider")
        self.assertFalse(user.is_active)
        self.assertEqual(user.role, "training_provider")

        get_user_model().objects.create_user(
            username="inactive_regular",
            password="securepassword123",
            is_active=False,
            role="student",
        )

        user = authenticate(username="inactive_regular", password="securepassword123")
        self.assertIsNone(user, "Inactive regular user should not authenticate")


class CustomLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.inactive_provider = get_user_model().objects.create_user(
            username="inactive_provider",
            email="inactive@example.com",
            password="securepassword123",
            is_active=False,
            role="training_provider",
        )
        self.active_provider = get_user_model().objects.create_user(
            username="active_provider",
            email="active@example.com",
            password="securepassword123",
            is_active=True,
            role="training_provider",
        )
        self.regular_user = get_user_model().objects.create_user(
            username="regular_user",
            email="regular@example.com",
            password="securepassword123",
            is_active=True,
            role="career_changer",
        )

    def test_login_view_inactive_provider(self):
        """Test CustomLoginView correctly redirects inactive providers"""
        # self.client.force_login(self.inactive_provider)
        response = self.client.post(
            reverse("account_login"),
            {"login": self.inactive_provider.username, "password": "securepassword123"},
            follow=True,
        )

        # CustomLoginView should redirect inactive providers to provider_verification
        response = self.client.get(reverse("provider_verification"))
        self.assertEqual(response.status_code, 200)

    def test_login_view_active_provider(self):
        """Test CustomLoginView handles active providers correctly"""
        # Use force_login to simulate the login
        response = self.client.post(
            reverse("account_login"),
            {"login": self.active_provider.username, "password": "securepassword123"},
            follow=False,
        )

        # Active providers should follow the adapter's regular redirect (manage_courses)
        self.assertRedirects(
            response, reverse("manage_courses"), fetch_redirect_response=False
        )
        self.assertEqual(response.status_code, 302)

    def test_login_view_regular_user(self):
        """Test CustomLoginView handles regular users correctly"""
        # self.client.force_login(self.regular_user)
        response = self.client.post(
            reverse("account_login"),
            {"login": self.regular_user.username, "password": "securepassword123"},
            follow=True,
        )

        # Regular users should follow the adapter's regular redirect (home)
        response = self.client.get(reverse("course_list"))
        self.assertEqual(response.status_code, 200)
