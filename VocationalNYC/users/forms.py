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
    # hidden field to confirm existing provider
    confirm_existing = forms.BooleanField(
        required=False, widget=forms.HiddenInput(), initial=False
    )

    phone_num = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "tel",
                "pattern": "[0-9]{10}",
                "title": "Please enter a valid 10-digit phone number",
                "placeholder": "Enter 10-digit phone number",
            }
        ),
        max_length=10,
        help_text="Enter a 10-digit phone number",
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(
            attrs={
                "placeholder": "https://www.example.com",
                "pattern": "https?://.+",
                "title": "Please include http:// or https:// in your URL",
            }
        ),
        help_text="Include http:// or https:// in your URL",
    )

    class Meta:
        model = Provider
        fields = [
            "name",
            "contact_firstname",
            "contact_lastname",
            "phone_num",
            "address",
            "open_time",
            "provider_desc",
            "website",
            "certificate",
            "confirm_existing",
        ]
        widgets = {
            "certificate": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_phone_num(self):
        phone = self.cleaned_data.get("phone_num")
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number.")
        return phone

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()

        # 1. Minimum length check
        if len(name) < 3:
            raise forms.ValidationError(
                "Business name must be at least 3 characters long."
            )

        # 2. Allow it when updating the Provider profile.
        if self.instance.pk and self.instance.name.lower() == name.lower():
            return name

        confirm_existing = self.data.get("confirm_existing") == "true"

        # 3. Try to find *another* Provider with the same name.
        try:
            existing_provider = Provider.objects.exclude(pk=self.instance.pk).get(
                name__iexact=name
            )
        except Provider.DoesNotExist:
            # No conflict => name is valid
            return name

        # 4. We found a conflicting Provider with the same name
        if existing_provider.user is None:
            # If user is not confirmed that it's truly the same business, raise:
            if not confirm_existing:
                raise forms.ValidationError(
                    "An unregistered provider with this name exists. "
                    "If this is your organization, please confirm to bind your account."
                )
            # Otherwise, user is confirming it belongs to them => allow name
            return name
        else:
            # If the conflicting Provider is already bound to *some* user
            raise forms.ValidationError(
                "The name of the organization already exists. Please modify the name."
            )

    def clean_certificate(self):
        certificate = self.cleaned_data.get("certificate")
        if certificate:
            if certificate.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Certificate file size must be under 5MB.")
        return certificate

    def clean_website(self):
        url = self.cleaned_data.get("website")
        if url:
            if not url.startswith(("http://", "https://")):
                raise forms.ValidationError(
                    "URL must start with 'http://' or 'https://'"
                )
            if "." not in url:
                raise forms.ValidationError("Please enter a valid domain name")
        return url

    def validate_unique(self):
        if self.cleaned_data.get("confirm_existing"):
            return
        super().validate_unique()


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["bio"]
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
