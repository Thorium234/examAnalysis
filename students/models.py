from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Student(models.Model):
    STREAM_CHOICES = (
        ('East', 'East'),
        ('West', 'West'),
        ('North', 'North'),
        ('South', 'South'),
    )
    
    FORM_CHOICES = (
        (1, 'Form 1'),
        (2, 'Form 2'),
        (3, 'Form 3'),
        (4, 'Form 4'),
    )
    
    admission_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    form_level = models.IntegerField(choices=FORM_CHOICES)
    stream = models.CharField(max_length=20, choices=STREAM_CHOICES)
    kcpe_marks = models.IntegerField(blank=True, null=True)
    phone_contact = models.CharField(max_length=20, blank=True, null=True)
    date_enrolled = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['form_level', 'stream', 'name']
        unique_together = ('form_level', 'stream', 'admission_number')
    
    def __str__(self):
        return f"{self.admission_number} - {self.name} (Form {self.form_level} {self.stream})"
    
    @property
    def class_name(self):
        return f"Form {self.form_level} {self.stream}"

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class ClassSubject(models.Model):
    form_level = models.IntegerField(choices=[(1, 'Form 1'), (2, 'Form 2'), (3, 'Form 3'), (4, 'Form 4')])
    stream = models.CharField(max_length=20)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    maximum_marks = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('form_level', 'stream', 'subject')
    
    def __str__(self):
        return f"Form {self.form_level} {self.stream} - {self.subject.name} (Max: {self.maximum_marks})"

class StudentSubject(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    is_enrolled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('student', 'subject')
    
    def __str__(self):
        return f"{self.student.name} - {self.subject.name}"