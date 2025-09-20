from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SubjectCategory(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Subject Categories'

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    category = models.ForeignKey(SubjectCategory, on_delete=models.SET_NULL, null=True, blank=True)
    is_mandatory = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    min_form_level = models.IntegerField(
        choices=[(i, f'Form {i}') for i in range(1, 5)],
        default=1,
        help_text="Minimum form level where this subject can be taken"
    )
    order = models.IntegerField(default=0, help_text="Display order within category")

    class Meta:
        ordering = ['category__order', 'order', 'name']

    def __str__(self):
        return self.name

    @property
    def category_name(self):
        return self.category.name if self.category else "Uncategorized"

class StudentSubjectEnrollment(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='subject_enrollments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='student_enrollments')
    date_enrolled = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    date_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'students_subject_enrollment'
        unique_together = ['student', 'subject']
        ordering = ['subject__category__order', 'subject__order']

    def __str__(self):
        return f"{self.student.name} - {self.subject.name}"

    @classmethod
    def get_available_subjects(cls, student):
        """Get subjects available for this student based on class and individual enrollment"""
        from students.models import ClassSubjectAvailability
        available_subjects = ClassSubjectAvailability.objects.filter(
            form_level=student.form_level,
            stream=student.stream,
            is_available=True
        ).values_list('subject_id', flat=True)
        
        return Subject.objects.filter(
            id__in=available_subjects
        ).exclude(
            studentsubjectenrollment__student=student,
            studentsubjectenrollment__is_active=False
        )
