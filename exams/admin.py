from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.contrib import messages
from .models import (
    Exam, ExamResult, StudentExamSummary, FormLevel,
    SubjectCategory, GradingSystem, GradingRange
)
from .forms import ExamForm

@admin.register(FormLevel)
class FormLevelAdmin(admin.ModelAdmin):
    list_display = ('number',)
    ordering = ['number']

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    form = ExamForm
    filter_horizontal = ('participating_forms',)
    
    list_display = ('name', 'get_exam_type', 'get_forms', 'year', 'term', 'is_active')
    list_filter = ('year', 'term', 'is_active', 'participating_forms')
    search_fields = ('name',)
    ordering = ('-year', '-term')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'year', 'term')
        }),
        ('Exam Type', {
            'fields': (
                'is_ordinary_exam', 'is_consolidated_exam',
                'is_kcse', 'is_year_average'
            ),
            'description': 'Select one exam type only'
        }),
        ('Participating Forms', {
            'fields': ('participating_forms',),
            'description': 'Select which forms will take this exam'
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
    
    def get_exam_type(self, obj):
        return obj.get_exam_type_display()
    get_exam_type.short_description = 'Exam Type'
    
    def get_forms(self, obj):
        return ", ".join([f"Form {form.number}" for form in obj.participating_forms.all()])
    get_forms.short_description = 'Participating Forms'
    
    class Media:
        js = ('js/exam_form.js',)

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'subject', 'total_marks', 'grade', 'points', 'rank_in_subject')
    list_filter = ('exam', 'subject', 'grade', 'student__form_level', 'student__stream')
    search_fields = ('student__name', 'student__admission_number', 'subject__name')
    ordering = ('exam', 'student', 'subject')

@admin.register(StudentExamSummary)
class StudentExamSummaryAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'total_marks', 'mean_grade', 'stream_position', 'overall_position')
    list_filter = ('exam', 'mean_grade', 'student__form_level', 'student__stream')
    search_fields = ('student__name', 'student__admission_number')
    ordering = ('exam', '-total_marks')

@admin.register(SubjectCategory)
class SubjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class GradingRangeInline(admin.TabularInline):
    model = GradingRange
    extra = 1
    min_num = 1
    ordering = ('-high_mark',)
    fields = ('low_mark', 'high_mark', 'grade', 'points')

@admin.register(GradingSystem)
class GradingSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'is_default', 'created_by', 'created_at')
    list_filter = ('category', 'is_active', 'is_default')
    search_fields = ('name', 'category__name')
    inlines = [GradingRangeInline]
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:grading_system_id>/manage-ranges/',
                self.admin_site.admin_view(self.manage_ranges_view),
                name='exams_gradingsystem_manage_ranges',
            ),
        ]
        return custom_urls + urls
    
    def manage_ranges_view(self, request, grading_system_id):
        grading_system = self.get_object(request, grading_system_id)
        
        if request.method == 'POST':
            if 'apply_sample' in request.POST:
                # Apply default ranges
                GradingRange.objects.filter(grading_system=grading_system).delete()
                for range_data in GradingSystem.get_default_ranges():
                    GradingRange.objects.create(
                        grading_system=grading_system,
                        low_mark=range_data['low'],
                        high_mark=range_data['high'],
                        grade=range_data['grade'],
                        points=range_data['points']
                    )
                messages.success(request, 'Applied sample grading ranges successfully.')
                return redirect('admin:exams_gradingsystem_change', grading_system_id)
            
            # Handle saving of manually entered ranges
            # Process form data here
            
        ranges = grading_system.ranges.all().order_by('-high_mark')
        context = {
            'title': f'Manage Grading Ranges - {grading_system.name}',
            'grading_system': grading_system,
            'ranges': ranges,
            'opts': self.model._meta,
            'original': grading_system,
            'has_view_permission': self.has_view_permission(request, grading_system),
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, grading_system),
            'has_delete_permission': self.has_delete_permission(request, grading_system),
        }
        return TemplateResponse(request, 'admin/exams/gradingsystem/manage_ranges.html', context)