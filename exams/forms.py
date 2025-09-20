from django import forms
from .models import Exam, FormLevel
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class ExamForm(forms.ModelForm):
    participating_forms = forms.ModelMultipleChoiceField(
        queryset=FormLevel.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select one or more forms that will participate in this exam"
    )
    
    class Meta:
        model = Exam
        fields = [
            'name', 'year', 'term',
            'is_ordinary_exam', 'is_consolidated_exam',
            'is_kcse', 'is_year_average',
            'participating_forms', 'is_active'
        ]
        widgets = {
            'year': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
            'is_ordinary_exam': forms.CheckboxInput(attrs={'class': 'exam-type-checkbox'}),
            'is_consolidated_exam': forms.CheckboxInput(attrs={'class': 'exam-type-checkbox'}),
            'is_kcse': forms.CheckboxInput(attrs={'class': 'exam-type-checkbox'}),
            'is_year_average': forms.CheckboxInput(attrs={'class': 'exam-type-checkbox'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        # Ensure at least one form level is selected
        participating_forms = cleaned_data.get('participating_forms')
        if not participating_forms:
            raise ValidationError(_("Please select at least one form level for the exam."))
            
        # Ensure at least one exam type is selected
        exam_types = [
            cleaned_data.get('is_ordinary_exam'),
            cleaned_data.get('is_consolidated_exam'),
            cleaned_data.get('is_kcse'),
            cleaned_data.get('is_year_average')
        ]
        
        if not any(exam_types):
            raise ValidationError(_("Please select one exam type."))
            
        if sum(bool(x) for x in exam_types) > 1:
            raise ValidationError(_("Please select only one exam type."))