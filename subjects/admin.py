# subjects/admin.py
from django.contrib import admin
from .models import Subject, SubjectPaper

class SubjectPaperInline(admin.TabularInline):
    model = SubjectPaper
    extra = 1

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'school', 'category', 'is_optional')
    list_filter = ('school', 'category', 'is_optional')
    search_fields = ('name', 'code')
    inlines = [SubjectPaperInline]

class SubjectPaperAdmin(admin.ModelAdmin):
    list_display = ('subject', 'paper_number', 'max_marks', 'contribution_percentage')
    list_filter = ('subject', 'subject__school')

admin.site.register(Subject, SubjectAdmin)
admin.site.register(SubjectPaper, SubjectPaperAdmin)
