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


class ProviderVerificationForm(forms.ModelForm):
    # hidden field to confirm existing provider
    confirm_existing = forms.BooleanField(
        required=False, 
        widget=forms.HiddenInput(),
        initial=False
    )

    class Meta:
        model = Provider
        fields = [
            "name",
            "contact_firstname",
            "contact_lastname",
            "phone_num",
            "address",
            "website",
            "provider_desc",
            "verification_file",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": "form-control"})
        self.fields["contact_firstname"].widget.attrs.update({"class": "form-control"})
        self.fields["contact_lastname"].widget.attrs.update({"class": "form-control"})
        self.fields["phone_num"].widget.attrs.update({"class": "form-control"})
        self.fields["address"].widget.attrs.update({"class": "form-control"})
        self.fields["website"].widget.attrs.update({"class": "form-control"})
        self.fields["provider_desc"].widget.attrs.update({"class": "form-control"})
        self.fields["verification_file"].required = True
        self.fields["verification_file"].widget.attrs.update(
            {"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}
        )

    def clean_phone_num(self):
        phone = self.cleaned_data.get("phone_num")
        if phone:
            # Remove any non-digit characters
            phone = "".join(filter(str.isdigit, phone))
            if len(phone) != 10:
                raise forms.ValidationError("Phone number must be 10 digits.")
        return phone

    def clean_name(self):
        name = self.cleaned_data.get("name")

        if len(name) < 3:
            raise forms.ValidationError(
                "Business name must be at least 3 characters long."
            )

        confirm_existing = False
        if self.data.get('confirm_existing') == 'true':
            confirm_existing = True
        print("clean_name: name =", name, "confirm_existing =", confirm_existing)
        if confirm_existing:
            print("clean_name: confirm_existing is true")
            print("name:", name)
            return name
        try:
            existing_provider = Provider.objects.get(name=name)
        except Provider.DoesNotExist:
            return name

        if existing_provider.user is None:
            print("clean_name: existing_provider.user is None")
            if not confirm_existing:
                raise forms.ValidationError(
                    "An unregistered provider with this name exists. "
                    "If this is your organization, please confirm to bind your account."
                )
            return name
        else:
            print(existing_provider.user)
            raise forms.ValidationError(
                "The name of the organization already exists. Please modify the name."
            )

    def clean_provider_desc(self):
        desc = self.cleaned_data.get("provider_desc")
        if desc and len(desc) < 50:
            raise forms.ValidationError(
                "Description must be at least 50 characters long."
            )
        return desc
