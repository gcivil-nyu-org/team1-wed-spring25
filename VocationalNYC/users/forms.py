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
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "modal-input",
                    "placeholder": "Enter your business name",
                }
            ),
            "contact_firstname": forms.TextInput(
                attrs={"class": "modal-input", "placeholder": "Enter your first name"}
            ),
            "contact_lastname": forms.TextInput(
                attrs={"class": "modal-input", "placeholder": "Enter your last name"}
            ),
            "phone_num": forms.TextInput(
                attrs={"class": "modal-input", "placeholder": "Enter contact number"}
            ),
            "address": forms.TextInput(
                attrs={"class": "modal-input", "placeholder": "Enter business address"}
            ),
            "open_time": forms.TextInput(
                attrs={
                    "class": "modal-input",
                    "placeholder": "Enter business hours, e.g. Mon–Fri 9am–6pm",
                }
            ),
            "provider_desc": forms.Textarea(
                attrs={
                    "class": "modal-input",
                    "placeholder": "Enter business description",
                    "rows": 4,
                }
            ),
            "website": forms.URLInput(
                attrs={"class": "modal-input", "placeholder": "Enter website URL"}
            ),
            "certificate": forms.FileInput(attrs={"class": "modal-input"}),
            "confirm_existing": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set required fields
        self.fields["name"].required = True
        self.fields["contact_firstname"].required = True
        self.fields["contact_lastname"].required = True
        self.fields["phone_num"].required = True

        # Optional fields
        self.fields["address"].required = True
        self.fields["open_time"].required = False
        self.fields["provider_desc"].required = False
        self.fields["website"].required = False
        self.fields["certificate"].required = True


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "modal-input", "placeholder": "Enter your first name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "modal-input", "placeholder": "Enter your last name"}
            ),
        }


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["bio"]
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
