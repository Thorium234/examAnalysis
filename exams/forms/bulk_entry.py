from django import forms
from django.core.exceptions import ValidationError
from exams.models import PaperResult, Exam
from students.models import Student, StudentSubjectEnrollment, Subject, SubjectPaper
from decimal import Decimal

class BulkPaperResultEntryForm(forms.Form):
    ENTRY_MODE_CHOICES = (
        ('standard', 'Standard (Use Paper Ratios)'),
        ('normal', 'Normal (Direct Entry)')
    )
    
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.filter(is_active=True),
        required=True
    )
    subject = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=True
    )
    entry_mode = forms.ChoiceField(
        choices=ENTRY_MODE_CHOICES,
        initial='standard',
        widget=forms.RadioSelect
    )
    
    # For normal mode
    max_marks = forms.DecimalField(
        required=False,
        min_value=0,
        help_text="Maximum marks for this paper"
    )
    
    # For standard mode
    paper = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter subjects based on user's permissions if needed
            self.fields['subject'].queryset = Subject.objects.filter(is_active=True)
        
        # Paper field will be populated via AJAX based on subject selection
        self.fields['paper'].queryset = SubjectPaper.objects.none()
        
    def clean(self):
        cleaned_data = super().clean()
        entry_mode = cleaned_data.get('entry_mode')
        max_marks = cleaned_data.get('max_marks')
        paper = cleaned_data.get('paper')
        
        if entry_mode == 'normal' and not max_marks:
            raise ValidationError("Maximum marks are required for normal entry mode")
        elif entry_mode == 'standard' and not paper:
            raise ValidationError("Paper selection is required for standard entry mode")
            
        return cleaned_data