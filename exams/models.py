from django.db import models
from django.contrib.auth import get_user_model
from students.models import Student, Subject, SubjectPaper
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json

User = get_user_model()

class SubjectCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Subject Categories"

class GradingSystem(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(SubjectCategory, on_delete=models.CASCADE, related_name='grading_systems')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.category.name} - {self.name} Grading System"
    
    def get_grade_and_points(self, marks):
        """Calculate grade and points based on the defined ranges"""
        if marks == -1:  # Special case for absent
            return 'X', 0
        elif marks == -2:  # Special case for disqualified
            return 'Y', 0
            
        ranges = self.ranges.all().order_by('-high_mark')
        for grade_range in ranges:
            if marks >= grade_range.low_mark and marks <= grade_range.high_mark:
                return grade_range.grade, grade_range.points
        return 'E', 1  # Default fallback
    
    @classmethod
    def get_default_ranges(cls):
        """Returns default grading ranges"""
        return [
            {'low': 80, 'high': 100, 'grade': 'A', 'points': 12},
            {'low': 75, 'high': 79, 'grade': 'A-', 'points': 11},
            {'low': 70, 'high': 74, 'grade': 'B+', 'points': 10},
            {'low': 65, 'high': 69, 'grade': 'B', 'points': 9},
            {'low': 60, 'high': 64, 'grade': 'B-', 'points': 8},
            {'low': 55, 'high': 59, 'grade': 'C+', 'points': 7},
            {'low': 50, 'high': 54, 'grade': 'C', 'points': 6},
            {'low': 45, 'high': 49, 'grade': 'C-', 'points': 5},
            {'low': 40, 'high': 44, 'grade': 'D+', 'points': 4},
            {'low': 35, 'high': 39, 'grade': 'D', 'points': 3},
            {'low': 30, 'high': 34, 'grade': 'D-', 'points': 2},
            {'low': 0, 'high': 29, 'grade': 'E', 'points': 1},
        ]
    
    class Meta:
        unique_together = ('category', 'name')

class GradingRange(models.Model):
    grading_system = models.ForeignKey(GradingSystem, on_delete=models.CASCADE, related_name='ranges')
    low_mark = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    high_mark = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade = models.CharField(max_length=2)
    points = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(12)])
    
    class Meta:
        ordering = ['-high_mark']
        unique_together = ('grading_system', 'grade')
        
    def __str__(self):
        return f"{self.grade} ({self.low_mark}-{self.high_mark})"
        
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.low_mark >= self.high_mark:
            raise ValidationError('Low mark must be less than high mark')

class FormLevel(models.Model):
    number = models.IntegerField(choices=[(1, 'Form 1'), (2, 'Form 2'), (3, 'Form 3'), (4, 'Form 4')])
    
    def __str__(self):
        return f"Form {self.number}"
        
    class Meta:
        ordering = ['number']

class Exam(models.Model):
    TERM_CHOICES = (
        (1, 'Term 1'),
        (2, 'Term 2'),
        (3, 'Term 3'),
    )
    
    name = models.CharField(max_length=200, help_text="Enter the name of the exam")
    year = models.IntegerField()
    term = models.IntegerField(choices=TERM_CHOICES)
    
    # Exam type boolean fields
    is_ordinary_exam = models.BooleanField(default=False, verbose_name="Ordinary Exam")
    is_consolidated_exam = models.BooleanField(default=False, verbose_name="Consolidated Exam")
    is_kcse = models.BooleanField(default=False, verbose_name="KCSE")
    is_year_average = models.BooleanField(default=False, verbose_name="Year Average")
    
    # Many-to-many relationship with form levels
    participating_forms = models.ManyToManyField(
        FormLevel,
        related_name='exams',
        help_text="Select which forms will participate in this exam"
    )
    
    date_created = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-year', '-term']
        
    def clean(self):
        from django.core.exceptions import ValidationError
        # Ensure at least one exam type is selected
        if not any([
            self.is_ordinary_exam,
            self.is_consolidated_exam,
            self.is_kcse,
            self.is_year_average
        ]):
            raise ValidationError("At least one exam type must be selected.")
            
        # Ensure only one type is selected
        exam_types_selected = sum([
            self.is_ordinary_exam,
            self.is_consolidated_exam,
            self.is_kcse,
            self.is_year_average
        ])
        if exam_types_selected > 1:
            raise ValidationError("Only one exam type can be selected.")
            
    def get_exam_type_display(self):
        if self.is_ordinary_exam:
            return "Ordinary Exam"
        elif self.is_consolidated_exam:
            return "Consolidated Exam"
        elif self.is_kcse:
            return "KCSE"
        elif self.is_year_average:
            return "Year Average"
        return "Unknown"
    
    def __str__(self):
        return f"{self.name} - Form {self.form_level} ({self.year} Term {self.term})"

class PaperResult(models.Model):
    STATUS_CHOICES = (
        ('P', 'Present'),
        ('A', 'Absent'),
        ('D', 'Disqualified')
    )
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    paper = models.ForeignKey(SubjectPaper, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(-2), MaxValueValidator(100)]
    )
    date_entered = models.DateTimeField(default=timezone.now)
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('exam', 'student', 'subject', 'paper')
        ordering = ['exam', 'student', 'subject', 'paper__paper_number']

class ExamResult(models.Model):
    STATUS_CHOICES = (
        ('P', 'Present'),
        ('A', 'Absent'),
        ('D', 'Disqualified')
    )
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    total_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(-2), MaxValueValidator(100)]
    )
    grade = models.CharField(max_length=2, blank=True)
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
        # No need to set total_marks for absent/disqualified as it's already set
        # during creation (-1 for absent, -2 for disqualified)
            
        # Get the active grading system for this subject
        grading_system = GradingSystem.objects.filter(
            subject=self.subject,
            is_active=True
        ).first()
        
        if grading_system:
            self.grade, self.points = grading_system.get_grade_and_points(self.total_marks)
        else:
            # Fallback to default grading if no custom system is defined
            self.grade = 'E'
            self.points = 1
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        status_map = {'P': '', 'A': '(Absent)', 'D': '(Disqualified)'}
        if self.status in ['A', 'D']:
            return f"{self.student.name} - {self.subject.name} {status_map[self.status]}"
        return f"{self.student.name} - {self.subject.name} - {self.total_marks}% ({self.grade})"

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
    attempted_subjects = models.IntegerField(default=0)  # New field for actual subjects attempted
    mean_points = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ('exam', 'student')
        ordering = ['exam', '-total_marks']
    
    # def calculate_mean_grade(self):
    #     """Calculate mean grade based on attempted subjects only"""
    #     if self.attempted_subjects > 0:
    #         mean_points = self.total_points / self.attempted_subjects
    #         # Find the most common grading system used across subjects
    #         results = ExamResult.objects.filter(exam=self.exam, student=self.student)
            
    #         for result in results:
    #             grading_system = GradingSystem.objects.filter(
    #                 subject=result.subject,
    #                 is_active=True
    #             ).first()
                
    #             if grading_system:
    #                 # Use the first valid grading system to determine mean grade
    #                 _, mean_grade = grading_system.get_grade_and_points(
    #                     mean_points * (100 / grading_system.grading_rules[0]['points'])  # Scale points to marks
    #                 )
    #                 return mean_grade
        
    #     return 'E'  # Default grade if no subjects attempted
    def calculate_mean_grade(self):
        """Calculate mean grade based on attempted subjects only"""
        if self.attempted_subjects > 0:
            self.mean_points = self.total_points / self.attempted_subjects
            # Find the most common grading system used across subjects
            results = ExamResult.objects.filter(exam=self.exam, student=self.student)

            for result in results:
                grading_system = GradingSystem.objects.filter(
                    subject=result.subject,
                    is_active=True
                ).first()

                if grading_system:
                    # Use the first valid grading system to determine mean grade
                    self.mean_grade, _ = grading_system.get_grade_and_points(
                        self.mean_points * (100 / grading_system.grading_rules['points'])  # Scale points to marks
                    )
                    return self.mean_grade

        self.mean_grade = 'E'  # Default grade if no subjects attempted
        return self.mean_grade
    
    def __str__(self):
        return f"{self.student.name} - {self.exam.name} Summary"