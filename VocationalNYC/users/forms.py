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

    confirm_existing = forms.BooleanField(required=False, widget=forms.HiddenInput())

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

    # def clean_name(self):
    #     name = self.cleaned_data.get("name")
    #     confirm_existing = self.cleaned_data.get("confirm_existing")

    #     print(f"Name: {name}, Confirm Existing: {confirm_existing}")
    #     sys.stdout.flush()

    #     if Provider.objects.filter(name=name).exists() and not confirm_existing:
    #         raise forms.ValidationError("A provider with this name already exists.")
    #     return name

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        confirm_existing = cleaned_data.get("confirm_existing")

        # if provider already exists and confirm_existing is not explicitly True, form is invalid
        if Provider.objects.filter(name=name).exists() and not confirm_existing:
            self.add_error(
                "name",
                "A provider with this name already exists. Please confirm you're affiliated.",
            )

    def validate_unique(self):
        """
        When confirm_existing is True, ignore the unique validation error of name.
        """
        confirm_existing = self.cleaned_data.get("confirm_existing")

        if not confirm_existing:
            try:
                super().validate_unique()
            except forms.ValidationError as e:
                if "name" in e.error_dict:
                    name = self.cleaned_data.get("name")
                    try:
                        provider = Provider.objects.get(name=name)
                        if provider.user is None:
                            return
                    except Provider.DoesNotExist:
                        pass
                raise


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
    bio = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        max_length=1000,
        required=False,
    )

    class Meta:
        model = Student
        fields = ["bio"]
