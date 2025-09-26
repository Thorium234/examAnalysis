# reports/forms.py

from django import forms
from .models import ReportSettings

class ReportSettingsForm(forms.ModelForm):
    """
    A ModelForm for the ReportSettings model.
    This form is used to create or update report settings for a school.
    """
    class Meta:
        model = ReportSettings
        fields = [
            'show_report_cover',
            'show_subject_grades',
            'show_student_remarks',
            'show_stream_rank',
            'show_overall_rank',
            'show_teacher_initials',
            'show_watermark',
            'show_school_fees_layout',
            'closing_date',
            'next_term_begins',
            'class_teacher_remarks',
            'principal_remarks',
        ]
        widgets = {
            'closing_date': forms.TextInput(attrs={'placeholder': 'E.g., 2024-12-01'}),
            'next_term_begins': forms.TextInput(attrs={'placeholder': 'E.g., 2025-01-15'}),
            'class_teacher_remarks': forms.Textarea(attrs={'rows': 4}),
            'principal_remarks': forms.Textarea(attrs={'rows': 4}),
        }
