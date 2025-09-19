from django.db import models
from django.contrib.auth import get_user_model
from students.models import Student
from exams.models import Exam
from django.utils import timezone

User = get_user_model()

class ReportTemplate(models.Model):
    REPORT_TYPES = (
        ('STUDENT_REPORT', 'Individual Student Report'),
        ('CLASS_MERIT_LIST', 'Class Merit List'),
        ('SUBJECT_ANALYSIS', 'Subject Analysis Report'),
        ('TEACHER_REPORT', 'Teacher Performance Report'),
    )
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class GeneratedReport(models.Model):
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='generated_reports')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=True, null=True)
    form_level = models.IntegerField(choices=[(1, 'Form 1'), (2, 'Form 2'), (3, 'Form 3'), (4, 'Form 4')], blank=True, null=True)
    stream = models.CharField(max_length=20, blank=True, null=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_generated = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-date_generated']
    
    def __str__(self):
        if self.student:
            return f"{self.template.name} - {self.student.name} - {self.exam.name}"
        else:
            return f"{self.template.name} - Form {self.form_level} {self.stream} - {self.exam.name}"

class Comment(models.Model):
    COMMENT_TYPES = (
        ('EXCELLENT', 'Excellent performance. Keep it up!'),
        ('GOOD', 'Good work. You can do better.'),
        ('AVERAGE', 'Average performance. Put more effort.'),
        ('BELOW_AVERAGE', 'Below average performance. You have the potential to do better.'),
        ('WEAK', 'Weak but has potential'),
        ('VERY_WEAK', 'Very weak. Needs serious improvement.'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='comments')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='comments')
    subject = models.ForeignKey('students.Subject', on_delete=models.CASCADE, blank=True, null=True)
    comment_type = models.CharField(max_length=20, choices=COMMENT_TYPES)
    custom_comment = models.TextField(blank=True, null=True)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('student', 'exam', 'subject')
    
    def __str__(self):
        if self.subject:
            return f"{self.student.name} - {self.subject.name} - {self.exam.name}"
        else:
            return f"{self.student.name} - General Comment - {self.exam.name}"
    
    @property
    def final_comment(self):
        if self.custom_comment:
            return self.custom_comment
        return dict(self.COMMENT_TYPES).get(self.comment_type, 'No comment')