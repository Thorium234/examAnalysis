from django.contrib import admin
from .models import ReportTemplate, GeneratedReport, Comment

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'is_active', 'created_by', 'date_created')
    list_filter = ('report_type', 'is_active')
    search_fields = ('name',)

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('template', 'exam', 'student', 'form_level', 'stream', 'generated_by', 'date_generated')
    list_filter = ('template__report_type', 'exam', 'form_level', 'stream')
    search_fields = ('student__name', 'student__admission_number')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'subject', 'comment_type', 'teacher')
    list_filter = ('comment_type', 'exam', 'subject', 'student__form_level', 'student__stream')
    search_fields = ('student__name', 'student__admission_number', 'custom_comment')