from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Provider, Student, Tag, CustomUser
from .forms import CustomSignupForm, ProviderVerificationForm, StudentProfileForm

class UserModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='career_changer'
        )

    def test_user_creation(self):
        self.assertTrue(isinstance(self.user, CustomUser))
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'career_changer')
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
            username='provider',
            email='provider@example.com',
            password='testpass123',
            role='training_provider'
        )

    def test_provider_creation(self):
        provider = Provider.objects.create(
            user=self.user,
            name="Test Provider",
            phone_num="1234567890",
            address="123 Test St"
        )
        self.assertEqual(provider.name, "Test Provider")
        self.assertFalse(provider.verification_status)

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_profile_view_get(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_provider_verification_view(self):
        self.user.role = 'training_provider'
        self.user.save()
        
        response = self.client.get(reverse('provider_verification'))
        self.assertEqual(response.status_code, 200)
        
        # Test form submission
        test_file = SimpleUploadedFile("test.pdf", b"file_content")
        form_data = {
            'name': 'Test Provider',
            'phone_num': '1234567890',
            'address': '123 Test St',
            'certificate': test_file
        }
        response = self.client.post(reverse('provider_verification'), form_data)
        self.assertEqual(response.status_code, 200)

class FormTests(TestCase):
    def test_custom_signup_form(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'career_changer'
        }
        form = CustomSignupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_provider_verification_form(self):
        form_data = {
            'name': 'Test Provider',
            'phone_num': '1234567890',
            'address': '123 Test St'
        }
        form = ProviderVerificationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_student_profile_form(self):
        form_data = {
            'bio': 'Test student bio'
        }
        form = StudentProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

class APITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='career_changer'
        )
        self.student = Student.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_add_tag(self):
        response = self.client.post(
            reverse('add_tag'),
            {'tag': 'python'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tag.objects.filter(name='python').exists())

    def test_remove_tag(self):
        tag = Tag.objects.create(name='python')
        self.student.tags.add(tag)
        
        response = self.client.post(
            reverse('remove_tag'),
            {'tag': 'python'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.student.tags.filter(name='python').exists())
