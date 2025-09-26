# exams/models.py
from django.db import models
from django.conf import settings  # Import settings to reference AUTH_USER_MODEL
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from school.models import School
from subjects.models import SubjectCategory # Centralized SubjectCategory model

# We no longer need this line.
# User = get_user_model()

class GradingSystem(models.Model):
    name = models.CharField(max_length=100)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='grading_systems')
    subject_category = models.ForeignKey(SubjectCategory, on_delete=models.CASCADE, related_name='grading_systems')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    # Use settings.AUTH_USER_MODEL to refer to the custom user model
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.name} - {self.name} Grading System"

class GradingRange(models.Model):
    grading_system = models.ForeignKey(GradingSystem, on_delete=models.CASCADE, related_name='grading_ranges')
    min_marks = models.IntegerField(validators=[MinValueValidator(0)])
    max_marks = models.IntegerField(validators=[MaxValueValidator(100)])
    grade = models.CharField(max_length=10)
    points = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('grading_system', 'min_marks', 'max_marks')
        ordering = ['-max_marks']

    def __str__(self):
        return f"{self.grading_system.name}: {self.grade} ({self.points} pts)"

class Exam(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='exams')
    name = models.CharField(max_length=100)
    form_level = models.IntegerField(choices=[(1, 'Form 1'), (2, 'Form 2'), (3, 'Form 3'), (4, 'Form 4')])
    year = models.IntegerField()
    term = models.IntegerField(choices=[(1, 'Term 1'), (2, 'Term 2'), (3, 'Term 3')])
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('school', 'name', 'form_level', 'year', 'term')
    
    def __str__(self):
        return f"{self.school.name} - {self.name} Form {self.form_level} ({self.year} Term {self.term})"

# This model will hold the results for each paper, e.g., PP1, PP2, PP3
class PaperResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='paper_results')
    # Using string references to avoid circular imports
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='paper_results')
    subject_paper = models.ForeignKey('subjects.SubjectPaper', on_delete=models.CASCADE, related_name='paper_results')
    marks = models.IntegerField(validators=[MinValueValidator(0)])
    
    class Meta:
        unique_together = ('exam', 'student', 'subject_paper')
    
    def __str__(self):
        return f"{self.student.name} - {self.subject_paper.subject.name} ({self.subject_paper.paper_number}) for {self.exam.name}"

# This model will hold the final, calculated marks for a subject.
class ExamResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_results')
    # Using string references
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='exam_results')
    subject = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='exam_results')
    final_marks = models.IntegerField()
    grade = models.CharField(max_length=10, blank=True)
    points = models.IntegerField(null=True, blank=True)
    subject_rank = models.IntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    # Use settings.AUTH_USER_MODEL to refer to the custom user model
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('exam', 'student', 'subject')
    
    def __str__(self):
        return f"{self.student.name}'s {self.subject.name} result for {self.exam.name}"

# This model will store the aggregated results for a student in a given exam.
class StudentExamSummary(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_summaries')
    # Using string references
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='exam_summaries')
    total_marks = models.IntegerField()
    mean_marks = models.FloatField()
    mean_grade = models.CharField(max_length=10)
    total_points = models.IntegerField()
    stream_position = models.IntegerField()
    overall_position = models.IntegerField()

    class Meta:
        unique_together = ('exam', 'student')
    
    def __str__(self):
        return f"{self.student.name}'s Summary for {self.exam.name}"
