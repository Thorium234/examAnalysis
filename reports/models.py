from django.db import models
from school.models import School

class ReportSettings(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='report_settings')
    show_report_cover = models.BooleanField(default=True)
    show_subject_grades = models.BooleanField(default=True)
    show_student_remarks = models.BooleanField(default=True)
    show_stream_rank = models.BooleanField(default=True)
    show_overall_rank = models.BooleanField(default=True)
    show_teacher_initials = models.BooleanField(default=True)
    show_watermark = models.BooleanField(default=True)
    show_school_fees_layout = models.BooleanField(default=False)
    
    # Text fields for remarks and dates
    closing_date = models.CharField(max_length=50, blank=True)
    next_term_begins = models.CharField(max_length=50, blank=True)
    class_teacher_remarks = models.TextField(blank=True)
    principal_remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"Report Settings for {self.school.name}"
