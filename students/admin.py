# students/admin.py
from django.contrib import admin
from .models import Student, StudentAdvancement

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'admission_number', 'school', 'form_level', 'stream', 'phone_contact', 'kcpe_marks')
    list_filter = ('school', 'form_level', 'stream')
    search_fields = ('name', 'admission_number')
    
class StudentAdvancementAdmin(admin.ModelAdmin):
    list_display = ('student', 'from_form_level', 'to_form_level', 'advancement_year', 'timestamp')
    list_filter = ('school', 'advancement_year')
    search_fields = ('student__name', 'student__admission_number')

admin.site.register(Student, StudentAdmin)
admin.site.register(StudentAdvancement, StudentAdvancementAdmin)
