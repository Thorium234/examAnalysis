from django.db import models
from django.conf import settings
from school.models import School

class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('single', 'Single Date'),
        ('range', 'Date Range'),
    ]

    PARTICIPANT_TYPE_CHOICES = [
        ('teachers', 'Teachers'),
        ('parents', 'Parents'),
        ('students', 'Students'),
        ('staff', 'Staff'),
        ('all', 'All'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=10, choices=EVENT_TYPE_CHOICES, default='single')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)  # Only for range events
    participants_type = models.CharField(max_length=20, choices=PARTICIPANT_TYPE_CHOICES, default='all')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='events', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.name