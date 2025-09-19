from django.contrib import admin
from .models import Exam, ExamResult, StudentExamSummary

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'form_level', 'year', 'term', 'is_active')
    list_filter = ('exam_type', 'form_level', 'year', 'term', 'is_active')
    search_fields = ('name',)
    ordering = ('-year', '-term', 'form_level')

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'subject', 'marks', 'grade', 'points', 'rank_in_subject')
    list_filter = ('exam', 'subject', 'grade', 'student__form_level', 'student__stream')
    search_fields = ('student__name', 'student__admission_number', 'subject__name')
    ordering = ('exam', 'student', 'subject')

@admin.register(StudentExamSummary)
class StudentExamSummaryAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'total_marks', 'mean_grade', 'stream_position', 'overall_position')
    list_filter = ('exam', 'mean_grade', 'student__form_level', 'student__stream')
    search_fields = ('student__name', 'student__admission_number')
    ordering = ('exam', '-total_marks')