# Location: exam_system/school/forms.py

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class UserCreationForm(forms.Form):
    """
    A form for creating a new user account with a designated role.
    Roles are set as a simple choice field for now.
    """
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )

    username = forms.CharField(max_length=150, help_text="Required. 150 characters or fewer.")
    email = forms.EmailField(help_text="Required. A valid email address.")
    password = forms.CharField(widget=forms.PasswordInput, help_text="Enter a strong password.")
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    def clean_username(self):
        """Ensures the username is not already taken."""
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already in use.")
        return username

    def clean_email(self):
        """Ensures the email is not already taken."""
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email
