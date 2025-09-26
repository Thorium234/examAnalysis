# Location: exam_system/students/models.py

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# We import other models only when necessary to prevent circular imports.
# In this case, we'll reference FormLevel using a string.

# We also need to import the School model to link students to a school.
from school.models import School

class Student(models.Model):
    """
    Model to store student information.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students')
    name = models.CharField(max_length=255)
    admission_number = models.CharField(max_length=50, unique=True)
    kcpe_marks = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(500)])
    stream = models.CharField(max_length=50, blank=True, null=True)
    
    # Correcting the circular import. We use a string reference 'exams.FormLevel'
    # instead of importing the model directly at the top of the file.
    form_level = models.ForeignKey(
        'exams.FormLevel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    
    subjects = models.ManyToManyField(
        'subjects.Subject',
        related_name='students'
    )
    phone_contact = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        ordering = ['admission_number']
        
    def __str__(self):
        return self.name

class StudentAdvancement(models.Model):
    """
    Model to track student advancement from one form level to another.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='advancements')
    
    # We use a string reference here as well to avoid circular imports.
    from_form_level = models.ForeignKey(
        'exams.FormLevel',
        on_delete=models.CASCADE,
        related_name='students_advanced_from'
    )
    
    to_form_level = models.ForeignKey(
        'exams.FormLevel',
        on_delete=models.CASCADE,
        related_name='students_advanced_to'
    )
    advancement_year = models.IntegerField()
    
    class Meta:
        verbose_name_plural = "Student Advancements"
        ordering = ['-advancement_year']

    def __str__(self):
        return f"{self.student.name} advanced from {self.from_form_level} to {self.to_form_level} in {self.advancement_year}"
