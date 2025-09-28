# Location: exam_system/school/models.py

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.text import slugify

class School(models.Model):
    name = models.CharField(max_length=255, unique=True)
    school_code = models.CharField(max_length=10, unique=True, help_text="Unique code for student authentication", null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Schools"

class FormLevel(models.Model):
    """
    Represents the Form levels in the school (e.g., Form 1, Form 2, Form 3, Form 4).
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='form_levels')
    number = models.IntegerField(choices=[(1, 'Form 1'), (2, 'Form 2'), (3, 'Form 3'), (4, 'Form 4')])

    class Meta:
        unique_together = ('school', 'number')
        ordering = ['number']

    def __str__(self):
        return f'Form {self.number} - {self.school.name}'

class Stream(models.Model):
    """
    Represents a specific stream within a Form Level (e.g., Form 1 North).
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='streams')
    name = models.CharField(max_length=50) # e.g., 'North', 'South', 'West', etc.
    form_level = models.ForeignKey(FormLevel, on_delete=models.CASCADE, related_name='streams')
    
    class Meta:
        unique_together = ('school', 'form_level', 'name')
        ordering = ['form_level', 'name']
        
    def __str__(self):
        return f'Form {self.form_level.number} {self.name}'
class Resource(models.Model):
    """
    Represents educational resources like PDFs, videos, etc.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)  # For external links
    resource_type = models.CharField(max_length=50, choices=[
        ('pdf', 'PDF Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('image', 'Image'),
        ('link', 'External Link'),
        ('other', 'Other'),
    ], default='other')
    subject = models.ForeignKey('subjects.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    form_level = models.ForeignKey(FormLevel, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    uploaded_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.school.name}"
