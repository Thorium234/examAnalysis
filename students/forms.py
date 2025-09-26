from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Student, StudentAdvancement
from school.models import FormLevel, Stream # Assuming FormLevel and Stream are in the school app

class StudentForm(forms.ModelForm):
    """
    Form for creating and updating a Student.
    """
    form_level = forms.ModelChoiceField(
        queryset=FormLevel.objects.all(),
        label="Form Level",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    stream = forms.ModelChoiceField(
        queryset=Stream.objects.all(),
        label="Stream",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Student
        fields = [
            'name',
            'admission_number',
            'form_level',
            'stream',
            'kcpe_marks',
            'phone_contact',
            'is_active',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply form-control class to all fields for consistent styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class StudentAdvancementForm(forms.ModelForm):
    """
    Form for advancing a student.
    """
    # These fields are pre-populated and should be read-only for the user.
    current_form = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'})
    )
    current_stream = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'})
    )

    class Meta:
        model = StudentAdvancement
        fields = [
            'academic_year',
            'student',
            'current_form',
            'current_stream',
            'next_form',
            'next_stream',
            'status',
            'remarks',
        ]
        widgets = {
            'student': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        current_form = cleaned_data.get('current_form')
        next_form = cleaned_data.get('next_form')
        status = cleaned_data.get('status')
        
        if status == 'promoted' and next_form <= current_form:
            raise forms.ValidationError(
                "For promotion, the next form must be higher than the current form."
            )
        elif status == 'retained' and next_form != current_form:
            raise forms.ValidationError(
                "For retention, the next form must be the same as the current form."
            )
        elif status == 'graduated' and current_form != 'Form 4': # Assuming Form 4 is the final form
            raise forms.ValidationError(
                "Only Form 4 students can be marked as graduated."
            )
            
        return cleaned_data

class StudentAdvancementBulkUploadForm(forms.Form):
    """
    Form for bulk uploading student advancement data from an Excel file.
    """
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload an Excel file (.xlsx) with student advancement data.',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'})
    )
    academic_year = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={'placeholder': 'YYYY', 'class': 'form-control'})
    )

    def clean_academic_year(self):
        academic_year = self.cleaned_data.get('academic_year')
        if not academic_year.isdigit() or len(academic_year) != 4:
            raise ValidationError("Academic year must be a 4-digit number (e.g., 2023).")
        return academic_year
