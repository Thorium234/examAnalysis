from django import forms
from django.contrib.auth import get_user_model
from .models import Event

User = get_user_model()

class EventForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'placeholder': 'Select participants'
        }),
        required=False
    )

    class Meta:
        model = Event
        fields = ['name', 'event_type', 'start_date', 'end_date', 'participants_type', 'participants']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event Name'
            }),
            'event_type': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'participants_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.school:
            self.fields['participants'].queryset = User.objects.filter(profile__school=self.user.school)

    def clean(self):
        cleaned_data = super().clean()
        event_type = cleaned_data.get('event_type')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if event_type == 'range' and not end_date:
            raise forms.ValidationError("End date is required for date range events")

        if end_date and start_date and end_date < start_date:
            raise forms.ValidationError("End date must be after start date")

        return cleaned_data