from allauth.account.forms import SignupForm
from django import forms

class CustomSignupForm(SignupForm):
    ROLE_CHOICES = (
        ("career_changer", "Career Changer"),
        ("training_provider", "Training Provider"),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    def save(self, request):
        # create the user
        user = super().save(request)
        # attachcustom fields
        user.role = self.cleaned_data['role']
        user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure email is required if you want
        self.fields['email'].required = True
        # self.fields['username'].required = True  # if needed
