# exams/forms.py
from django import forms
from .models import (
    Exam, ExamResult, SubjectCategory,
    GradingSystem, GradingRange, PaperResult
)
from subjects.models import SubjectPaperRatio, Subject
from school.models import FormLevel
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

class ExamResultForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = ['student', 'subject', 'final_marks']

class SubjectCategoryForm(forms.ModelForm):
    class Meta:
        model = SubjectCategory
        fields = ['name']

class GradingSystemForm(forms.ModelForm):
    class Meta:
        model = GradingSystem
        fields = ['name', 'subject_category']

class GradingRangeForm(forms.ModelForm):
    class Meta:
        model = GradingRange
        fields = ['grade', 'min_marks', 'max_marks', 'points']

class FormLevelForm(forms.ModelForm):
    class Meta:
        model = FormLevel
        fields = ['number']
        
class PaperResultForm(forms.ModelForm):
    class Meta:
        model = PaperResult
        fields = ['exam', 'student', 'subject_paper', 'marks']

class SubjectPaperRatioForm(forms.ModelForm):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the subject for which to configure paper ratios"
    )

    class Meta:
        model = SubjectPaperRatio
        fields = [
            'subject',
            'paper1_max_marks', 'paper1_contribution',
            'paper2_max_marks', 'paper2_contribution',
            'paper3_max_marks', 'paper3_contribution',
        ]
        widgets = {
            'paper1_max_marks': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 100'}),
            'paper1_contribution': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 50.00', 'step': '0.01'}),
            'paper2_max_marks': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 100'}),
            'paper2_contribution': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 50.00', 'step': '0.01'}),
            'paper3_max_marks': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 80'}),
            'paper3_contribution': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 33.33', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            self.fields['subject'].queryset = Subject.objects.filter(school=user.school)

    def clean(self):
        cleaned_data = super().clean()
        subject = cleaned_data.get('subject')

        # Check if subject already has paper ratios
        if subject and SubjectPaperRatio.objects.filter(subject=subject).exists():
            if not self.instance.pk:  # Only for new instances
                raise forms.ValidationError("This subject already has paper ratios configured.")

        # Validate that if max_marks is provided, contribution is also provided and vice versa
        for paper_num in ['1', '2', '3']:
            max_marks = cleaned_data.get(f'paper{paper_num}_max_marks')
            contribution = cleaned_data.get(f'paper{paper_num}_contribution')

            if (max_marks and not contribution) or (contribution and not max_marks):
                raise forms.ValidationError(f"Paper {paper_num}: Both max marks and contribution percentage must be provided together.")

        return cleaned_data
