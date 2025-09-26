# students/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Student, StudentAdvancement

class StudentForm(forms.ModelForm):
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
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class StudentAdvancementForm(forms.ModelForm):
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
            'current_form': forms.HiddenInput(),
            'current_stream': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        current_form = cleaned_data.get('current_form')
        next_form = cleaned_data.get('next_form')
        status = cleaned_data.get('status')
        
        if status == 'promoted' and next_form <= current_form:
            raise forms.ValidationError(
                "For promotion, next form must be higher than current form."
            )
        elif status == 'retained' and next_form != current_form:
            raise forms.ValidationError(
                "For retention, next form must be same as current form."
            )
        elif status == 'graduated' and current_form != 4:
            raise forms.ValidationError(
                "Only Form 4 students can be marked as graduated."
            )
            
        return cleaned_data

class StudentAdvancementBulkUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload an Excel file (.xlsx) with student advancement data',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'})
    )
    academic_year = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={'placeholder': 'YYYY', 'class': 'form-control'})
    )
