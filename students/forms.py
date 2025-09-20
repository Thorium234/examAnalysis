from django import forms
from .models import SubjectPaper, SubjectPaperRatio, StudentAdvancement, Student

class SubjectPaperForm(forms.ModelForm):
    class Meta:
        model = SubjectPaper
        fields = ['name', 'paper_number', 'max_marks', 'is_active']
        widgets = {
            'max_marks': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
        }

class SubjectPaperRatioForm(forms.ModelForm):
    class Meta:
        model = SubjectPaperRatio
        fields = ['paper', 'contribution_percentage', 'is_active']
        widgets = {
            'contribution_percentage': forms.NumberInput(
                attrs={'step': '0.01', 'min': '0', 'max': '100'}
            ),
        }
        
    def clean_contribution_percentage(self):
        percentage = self.cleaned_data['contribution_percentage']
        if percentage < 0 or percentage > 100:
            raise forms.ValidationError('Percentage must be between 0 and 100')
        return percentage

class StudentAdvancementForm(forms.ModelForm):
    class Meta:
        model = StudentAdvancement
        fields = ['student', 'academic_year', 'current_form', 'current_stream',
                 'next_form', 'next_stream', 'status', 'remarks']
        widgets = {
            'academic_year': forms.TextInput(attrs={'placeholder': 'YYYY'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(is_active=True)
        
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
        help_text='Upload an Excel file (.xlsx) with student advancement data'
    )
    academic_year = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={'placeholder': 'YYYY'})
    )