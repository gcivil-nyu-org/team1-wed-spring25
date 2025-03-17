from allauth.account.forms import SignupForm
from django import forms
from .models import Provider

# from .models import CustomUser, Student

class CustomSignupForm(SignupForm):
    ROLE_CHOICES = (
        ("career_changer", "Career Changer"),
        ("training_provider", "Training Provider"),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    def save(self, request):
        user = super().save(request)
        user.role = self.cleaned_data["role"]
        user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True


class ProviderVerificationForm(forms.Form):
    business_name = forms.CharField(
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter your business name'})
    )
    business_address = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter business address'})
    )
    website = forms.URLField(
        required=False, 
        widget=forms.URLInput(attrs={'placeholder': 'Enter website URL'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter business description', 'rows': 1, 'style': 'resize: none;'}), 
        required=False
    )
    first_name = forms.CharField(
        max_length=50, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'})
    )
    last_name = forms.CharField(
        max_length=50, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter your last name'})
    )
    contact_number = forms.CharField(
        max_length=15, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter contact number'})
    )
    certificate = forms.FileField(required=True)

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if not contact_number.isdigit():
            raise forms.ValidationError("Contact number must contain only digits.")
        return contact_number

    def clean_certificate(self):
        certificate = self.cleaned_data.get('certificate')
        if certificate:
            if certificate.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Certificate file size must be under 5MB.")
        return certificate
