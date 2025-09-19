from django.contrib import admin
from .models import Student, Subject, ClassSubject, StudentSubject

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'name', 'form_level', 'stream', 'kcpe_marks', 'is_active')
    list_filter = ('form_level', 'stream', 'is_active')
    search_fields = ('admission_number', 'name', 'phone_contact')
    ordering = ('form_level', 'stream', 'name')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('form_level', 'stream', 'subject', 'maximum_marks', 'is_active')
    list_filter = ('form_level', 'stream', 'subject', 'is_active')
    ordering = ('form_level', 'stream', 'subject')

@admin.register(StudentSubject)
class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'is_enrolled')
    list_filter = ('subject', 'is_enrolled', 'student__form_level', 'student__stream')
    search_fields = ('student__name', 'student__admission_number', 'subject__name')