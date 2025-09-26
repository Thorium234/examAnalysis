# exams/forms/result_entry.py
from django import forms
from exams.models import PaperResult

class PaperResultRow(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.HiddenInput
    )
    admission_number = forms.CharField(
        disabled=True,
        required=False
    )
    name = forms.CharField(
        disabled=True,
        required=False
    )
    marks = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'step': '0.5'})
    )
    status = forms.ChoiceField(
        choices=PaperResult.STATUS_CHOICES,
        initial='P',
        widget=forms.Select(attrs={'class': 'status-select'})
    )
    
    def __init__(self, *args, **kwargs):
        max_marks = kwargs.pop('max_marks', 100)
        super().__init__(*args, **kwargs)
        self.fields['marks'].max_value = max_marks
        if 'initial' in kwargs:
            student = kwargs['initial'].get('student')
            if student:
                self.fields['admission_number'].initial = student.admission_number
                self.fields['name'].initial = student.name
        
    def clean_marks(self):
        marks = self.cleaned_data.get('marks')
        status = self.cleaned_data.get('status')
        
        if status == 'P' and marks is None:
            raise ValidationError("Marks are required for present students")
        elif status in ['A', 'D'] and marks is not None:
            raise ValidationError("Marks should not be entered for absent or disqualified students")
            
        return marks

class BulkResultUploadForm(forms.Form):
    result_file = forms.FileField(
        help_text="Upload Excel or CSV file with results. Format: Admission Number, Marks, Status (P/A/D)"
    )
    has_headers = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Check if file has header row"
    )
    
    def clean_result_file(self):
        file = self.cleaned_data['result_file']
        ext = file.name.split('.')[-1].lower()
        
        if ext not in ['csv', 'xlsx', 'xls']:
            raise ValidationError("Only CSV and Excel files are allowed")
            
        return file