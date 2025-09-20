from django.contrib import admin
from .models import Subject, SubjectCategory, StudentSubjectEnrollment

@admin.register(SubjectCategory)
class SubjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)
    ordering = ('order', 'name')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'is_mandatory', 'min_form_level')
    list_filter = ('category', 'is_mandatory', 'min_form_level')
    search_fields = ('name', 'code')
    ordering = ('category__order', 'order', 'name')

@admin.register(StudentSubjectEnrollment)
class StudentSubjectEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'is_active', 'date_enrolled', 'date_modified', 'modified_by')
    list_filter = ('is_active', 'subject__category')
    search_fields = ('student__name', 'student__admission_number', 'subject__name')
    ordering = ('-date_modified',)
    raw_id_fields = ('student', 'subject', 'modified_by')
