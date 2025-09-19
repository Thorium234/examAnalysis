from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, TeacherSubject, TeacherClass

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'phone_number', 'employee_id'),
        }),
    )

@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject_name')
    list_filter = ('subject_name',)
    search_fields = ('teacher__username', 'teacher__first_name', 'teacher__last_name', 'subject_name')

@admin.register(TeacherClass)
class TeacherClassAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'form_level', 'stream', 'is_class_teacher')
    list_filter = ('form_level', 'stream', 'is_class_teacher')
    search_fields = ('teacher__username', 'teacher__first_name', 'teacher__last_name')