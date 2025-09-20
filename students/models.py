from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from subjects.models import Subject, StudentSubjectEnrollment

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
    
    enrolled_subjects = models.ManyToManyField(
        'subjects.Subject',
        related_name='enrolled_students',
        through='subjects.StudentSubjectEnrollment'
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
    
    @property
    def full_name(self):
        return self.name

class SubjectPaper(models.Model):
    name = models.CharField(max_length=50, help_text="e.g., Paper 1, Paper 2")
    paper_number = models.IntegerField(help_text="e.g., 1 for Paper 1")
    max_marks = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Maximum marks for this paper"
    )
    is_active = models.BooleanField(default=True)
    
class StudentAdvancement(models.Model):
    ADVANCEMENT_STATUS = [
        ('promoted', 'Promoted'),
        ('retained', 'Retained'),
        ('conditional', 'Conditional Promotion'),
        ('graduated', 'Graduated'),
        ('discontinued', 'Discontinued'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='advancements')
    academic_year = models.CharField(max_length=10)  # e.g., "2025"
    current_form = models.IntegerField(choices=Student.FORM_CHOICES)
    current_stream = models.CharField(max_length=20, choices=Student.STREAM_CHOICES)
    next_form = models.IntegerField(choices=Student.FORM_CHOICES)
    next_stream = models.CharField(max_length=20, choices=Student.STREAM_CHOICES)
    status = models.CharField(max_length=20, choices=ADVANCEMENT_STATUS)
    decision_date = models.DateField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'academic_year']
        ordering = ['-academic_year', 'current_form', 'current_stream', 'student__admission_number']
        verbose_name = 'Student Advancement Record'
        verbose_name_plural = 'Student Advancement Records'

    def __str__(self):
        return f"{self.student.admission_number} - {self.academic_year} ({self.status})"

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    category = models.ForeignKey('exams.SubjectCategory', on_delete=models.SET_NULL, null=True, blank=True)
    grading_system = models.ForeignKey('exams.GradingSystem', on_delete=models.SET_NULL, null=True, blank=True)
    papers = models.ManyToManyField(SubjectPaper, through='SubjectPaperRatio')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        # If category exists but no grading system is set, use the default one for the category
        if self.category and not self.grading_system:
            default_grading = self.category.grading_systems.filter(is_default=True).first()
            if default_grading:
                self.grading_system = default_grading
        super().save(*args, **kwargs)

class SubjectPaperRatio(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    paper = models.ForeignKey(SubjectPaper, on_delete=models.CASCADE)
    contribution_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage contribution to final mark (e.g., 50 for 50%)",
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    is_active = models.BooleanField(default=True)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Check if total contribution for the subject doesn't exceed 100%
        total = SubjectPaperRatio.objects.filter(
            subject=self.subject,
            is_active=True
        ).exclude(pk=self.pk).aggregate(
            total=models.Sum('contribution_percentage')
        )['total'] or 0
        
        if total + self.contribution_percentage > 100:
            raise ValidationError(
                'Total contribution percentage cannot exceed 100%. '
                f'Current total: {total}%, Attempting to add: {self.contribution_percentage}%'
            )
    
    def __str__(self):
        return f"{self.subject.name} - {self.paper.name} ({self.contribution_percentage}%)"
    
    class Meta:
        unique_together = ('subject', 'paper')
        ordering = ['subject', 'paper__paper_number']

class ClassSubjectAvailability(models.Model):
    form_level = models.IntegerField(choices=[(1, 'Form 1'), (2, 'Form 2'), (3, 'Form 3'), (4, 'Form 4')])
    stream = models.CharField(max_length=20, choices=Student.STREAM_CHOICES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('form_level', 'stream', 'subject')
        verbose_name_plural = 'Class Subject Availabilities'
        
    def __str__(self):
        return f"Form {self.form_level} {self.stream} - {self.subject.name}"


