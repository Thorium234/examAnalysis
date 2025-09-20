from django.contrib import admin
from .models import Student, StudentAdvancement, ClassSubjectAvailability, SubjectPaper
from .forms import SubjectPaperForm

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'name', 'form_level', 'stream', 'kcpe_marks', 'is_active')
    list_filter = ('form_level', 'stream', 'is_active')
    search_fields = ('admission_number', 'name', 'phone_contact')
    ordering = ('form_level', 'stream', 'name')

@admin.register(SubjectPaper)
class SubjectPaperAdmin(admin.ModelAdmin):
    form = SubjectPaperForm
    list_display = ('name', 'paper_number', 'max_marks', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('paper_number',)

@admin.register(StudentAdvancement)
class StudentAdvancementAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'current_form', 'next_form', 'status')
    list_filter = ('status', 'academic_year', 'current_form')
    search_fields = ('student__name', 'student__admission_number')

@admin.register(ClassSubjectAvailability)
class ClassSubjectAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('subject', 'form_level', 'stream', 'is_available')
    list_filter = ('form_level', 'stream', 'is_available')
    search_fields = ('subject__name',)
