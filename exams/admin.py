# exams/admin.py
from django.contrib import admin
from .models import (
    Exam,
    SubjectCategory,
    GradingSystem,
    GradingRange,
    PaperResult,
    ExamResult,
    StudentExamSummary,
)

class GradingRangeInline(admin.TabularInline):
    model = GradingRange
    extra = 1

class GradingSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'subject_category', 'is_active', 'is_default')
    list_filter = ('school', 'is_active', 'is_default')
    inlines = [GradingRangeInline]

class SubjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    list_filter = ('school',)

class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'form_level', 'year', 'term', 'is_published')
    list_filter = ('school', 'form_level', 'year', 'term', 'is_published')
    search_fields = ('name',)

class PaperResultAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'subject_paper', 'marks')
    list_filter = ('exam__school', 'exam', 'subject_paper')
    search_fields = ('student__name', 'student__admission_number')

class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'subject', 'final_marks', 'grade', 'points', 'subject_rank', 'teacher')
    list_filter = ('exam__school', 'exam', 'subject', 'teacher')
    search_fields = ('student__name', 'student__admission_number')
    
class StudentExamSummaryAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'total_marks', 'mean_grade', 'overall_position')
    list_filter = ('exam__school', 'exam')
    search_fields = ('student__name', 'student__admission_number')

admin.site.register(Exam, ExamAdmin)
admin.site.register(SubjectCategory, SubjectCategoryAdmin)
admin.site.register(GradingSystem, GradingSystemAdmin)
admin.site.register(PaperResult, PaperResultAdmin)
admin.site.register(ExamResult, ExamResultAdmin)
admin.site.register(StudentExamSummary, StudentExamSummaryAdmin)
