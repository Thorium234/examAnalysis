# Location: exam_system/school/models.py

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.text import slugify

class School(models.Model):
    name = models.CharField(max_length=255, unique=True)
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
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('school', 'name')
        ordering = ['name']
        
    def __str__(self):
        return f'{self.name} - {self.school.name}'

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
        return f'{self.form_level.name} {self.name}'
