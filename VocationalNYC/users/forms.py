# users/forms.py
from allauth.account.forms import SignupForm
from django import forms

class StudentSignupForm(SignupForm):
    """
    A custom signup form that automatically assigns role='S' (Student).
    """
    def save(self, request):
        user = super().save(request)
        user.role = 'S'
        user.save()
        return user

class ProviderSignupForm(SignupForm):
    """
    A custom signup form that automatically assigns role='P' (Provider).
    """
    def save(self, request):
        user = super().save(request)
        user.role = 'P'
        user.save()
        return user
