from django.db import models
from django.contrib.auth import get_user_model
from students.models import Student, Subject
from django.utils import timezone

User = get_user_model()

class Exam(models.Model):
    EXAM_TYPES = (
        ('MID_YEAR', 'Mid Year Exam'),
        ('END_TERM', 'End Term Exam'),
        ('AVERAGE', 'Average Exam'),
        ('CAT', 'Continuous Assessment Test'),
    )
    
    TERM_CHOICES = (
        (1, 'Term 1'),
        (2, 'Term 2'),
        (3, 'Term 3'),
    )
    
    name = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    year = models.IntegerField()
    term = models.IntegerField(choices=TERM_CHOICES)
    form_level = models.IntegerField(choices=[(1, 'Form 1'), (2, 'Form 2'), (3, 'Form 3'), (4, 'Form 4')])
    date_created = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('name', 'exam_type', 'year', 'term', 'form_level')
        ordering = ['-year', '-term', 'form_level']
    
    def __str__(self):
        return f"{self.name} - Form {self.form_level} ({self.year} Term {self.term})"

class ExamResult(models.Model):
    GRADE_CHOICES = (
        ('A', 'A (80-100)'),
        ('A-', 'A- (75-79)'),
        ('B+', 'B+ (70-74)'),
        ('B', 'B (65-69)'),
        ('B-', 'B- (60-64)'),
        ('C+', 'C+ (55-59)'),
        ('C', 'C (50-54)'),
        ('C-', 'C- (45-49)'),
        ('D+', 'D+ (40-44)'),
        ('D', 'D (35-39)'),
        ('D-', 'D- (30-34)'),
        ('E', 'E (0-29)'),
        ('X', 'X (Absent)'),
    )
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks = models.IntegerField()
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    points = models.IntegerField(blank=True, null=True)
    deviation = models.IntegerField(blank=True, null=True)
    rank_in_subject = models.IntegerField(blank=True, null=True)
    total_students_in_subject = models.IntegerField(blank=True, null=True)
    date_entered = models.DateTimeField(default=timezone.now)
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('exam', 'student', 'subject')
        ordering = ['exam', 'student', 'subject']
    
    def save(self, *args, **kwargs):
        # Auto-calculate grade and points based on marks
        self.grade = self.calculate_grade(self.marks)
        self.points = self.calculate_points(self.grade)
        super().save(*args, **kwargs)
    
    def calculate_grade(self, marks):
        if marks >= 80:
            return 'A'
        elif marks >= 75:
            return 'A-'
        elif marks >= 70:
            return 'B+'
        elif marks >= 65:
            return 'B'
        elif marks >= 60:
            return 'B-'
        elif marks >= 55:
            return 'C+'
        elif marks >= 50:
            return 'C'
        elif marks >= 45:
            return 'C-'
        elif marks >= 40:
            return 'D+'
        elif marks >= 35:
            return 'D'
        elif marks >= 30:
            return 'D-'
        else:
            return 'E'
    
    def calculate_points(self, grade):
        points_map = {
            'A': 12, 'A-': 11, 'B+': 10, 'B': 9, 'B-': 8,
            'C+': 7, 'C': 6, 'C-': 5, 'D+': 4, 'D': 3,
            'D-': 2, 'E': 1, 'X': 0
        }
        return points_map.get(grade, 1)
    
    def __str__(self):
        return f"{self.student.name} - {self.subject.name} - {self.marks}% ({self.grade})"

class StudentExamSummary(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='student_summaries')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_summaries')
    total_marks = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    mean_marks = models.FloatField(default=0.0)
    mean_grade = models.CharField(max_length=2, blank=True)
    stream_position = models.IntegerField(blank=True, null=True)
    overall_position = models.IntegerField(blank=True, null=True)
    total_students_in_stream = models.IntegerField(blank=True, null=True)
    total_students_overall = models.IntegerField(blank=True, null=True)
    subjects_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('exam', 'student')
        ordering = ['exam', '-total_marks']
    
    def calculate_mean_grade(self):
        if self.subjects_count > 0:
            mean_points = self.total_points / self.subjects_count
            if mean_points >= 11.5:
                return 'A'
            elif mean_points >= 10.5:
                return 'A-'
            elif mean_points >= 9.5:
                return 'B+'
            elif mean_points >= 8.5:
                return 'B'
            elif mean_points >= 7.5:
                return 'B-'
            elif mean_points >= 6.5:
                return 'C+'
            elif mean_points >= 5.5:
                return 'C'
            elif mean_points >= 4.5:
                return 'C-'
            elif mean_points >= 3.5:
                return 'D+'
            elif mean_points >= 2.5:
                return 'D'
            elif mean_points >= 1.5:
                return 'D-'
            else:
                return 'E'
        return 'E'
    
    def __str__(self):
        return f"{self.student.name} - {self.exam.name} Summary"