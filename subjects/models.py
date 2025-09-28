# subjects/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from school.models import School

class SubjectCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='subject_categories')

    class Meta:
        verbose_name_plural = "Subject Categories"
        unique_together = ('name', 'school')

    def __str__(self):
        return self.name

class Subject(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    category = models.ForeignKey(
        SubjectCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects'
    )
    form_levels = models.ManyToManyField('school.FormLevel', related_name='subjects', blank=True)
    is_optional = models.BooleanField(default=False)

    class Meta:
        unique_together = ('school', 'name', 'code')
    
    def __str__(self):
        return self.name

class SubjectPaper(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='papers')
    paper_number = models.CharField(max_length=10, help_text="e.g., PP1, PP2, PP3")
    max_marks = models.IntegerField(validators=[MinValueValidator(0)])
    student_contribution_marks = models.IntegerField(
        help_text="Student contribution marks to the final subject score.",
        validators=[MinValueValidator(0)],
        default=50
    )
    
    class Meta:
        unique_together = ('subject', 'paper_number')
    
    def __str__(self):
        return f"{self.subject.name} - {self.paper_number}"
