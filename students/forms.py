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
        ]
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Apply form-control class to all fields for consistent styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        if self.user and self.user.school:
            self.fields['form_level'].queryset = FormLevel.objects.filter(school=self.user.school)
            self.fields['stream'].queryset = Stream.objects.filter(school=self.user.school)



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
