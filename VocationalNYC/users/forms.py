from allauth.account.forms import SignupForm
from django import forms
from .models import Provider, CustomUser, Student

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

class ProviderVerificationForm(forms.ModelForm):
    phone_num = forms.CharField(
        widget=forms.TextInput(attrs={
            'type': 'tel', 
            'pattern': '[0-9]{10}',
            'title': 'Please enter a valid 10-digit phone number',
            'placeholder': 'Enter 10-digit phone number'
        }),
        max_length=10,
        help_text='Enter a 10-digit phone number'
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'placeholder': 'https://www.example.com',
            'pattern': 'https?://.+',
            'title': 'Please include http:// or https:// in your URL'
        }),
        help_text='Include http:// or https:// in your URL'
    )

    class Meta:
        model = Provider
        fields = ['name', 'contact_firstname', 'contact_lastname', 'phone_num', 'address', 'open_time', 'provider_desc', 'website', 'certificate']

    def clean_phone_num(self):
        phone = self.cleaned_data.get('phone_num')
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number.")
        return phone

    def clean_certificate(self):
        certificate = self.cleaned_data.get('certificate')
        if certificate:
            if certificate.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Certificate file size must be under 5MB.")
        return certificate

    def clean_website(self):
        url = self.cleaned_data.get('website')
        if url:
            if not url.startswith(('http://', 'https://')):
                raise forms.ValidationError("URL must start with 'http://' or 'https://'")
            if not '.' in url:
                raise forms.ValidationError("Please enter a valid domain name")
        return url

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
