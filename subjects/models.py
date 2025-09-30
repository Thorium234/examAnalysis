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
    is_active = models.BooleanField(default=True)

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

class SubjectPaperRatio(models.Model):
    subject = models.OneToOneField(Subject, on_delete=models.CASCADE, related_name='paper_ratio')

    # Paper 1 configuration
    paper1_max_marks = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Maximum marks for Paper 1",
        blank=True,
        null=True
    )
    paper1_contribution = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage contribution of Paper 1 to final marks",
        blank=True,
        null=True
    )

    # Paper 2 configuration
    paper2_max_marks = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Maximum marks for Paper 2",
        blank=True,
        null=True
    )
    paper2_contribution = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage contribution of Paper 2 to final marks",
        blank=True,
        null=True
    )

    # Paper 3 configuration
    paper3_max_marks = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Maximum marks for Paper 3",
        blank=True,
        null=True
    )
    paper3_contribution = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage contribution of Paper 3 to final marks",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Subject Paper Ratio"
        verbose_name_plural = "Subject Paper Ratios"

    def __str__(self):
        return f"{self.subject.name} Paper Ratios"

    def get_paper_configs(self):
        """Return a list of (max_marks, contribution) tuples for papers that are configured"""
        configs = []
        if self.paper1_max_marks is not None and self.paper1_contribution is not None:
            configs.append((self.paper1_max_marks, self.paper1_contribution))
        if self.paper2_max_marks is not None and self.paper2_contribution is not None:
            configs.append((self.paper2_max_marks, self.paper2_contribution))
        if self.paper3_max_marks is not None and self.paper3_contribution is not None:
            configs.append((self.paper3_max_marks, self.paper3_contribution))
        return configs
