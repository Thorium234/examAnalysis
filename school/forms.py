# Location: exam_system/school/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import School, FormLevel, Stream

class UserCreationForm(forms.Form):
    """
    A simple form to create a new user account with a specific role.
    """
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('principal', 'Principal'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)

class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['name', 'location', 'logo', 'address', 'phone_number', 'email']

class FormLevelForm(forms.ModelForm):
    """
    Form for creating and updating a FormLevel model.
    """
    class Meta:
        model = FormLevel
        fields = ['name']

class StreamForm(forms.ModelForm):
    """
    Form for creating and updating a Stream model.
    """
    class Meta:
        model = Stream
        fields = ['name', 'form_level']
