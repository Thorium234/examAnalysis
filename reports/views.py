from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import ReportSettings
from school.models import School

# Mixin to restrict views to school admins and HODs
class SchoolAdminOrHODRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return user.profile.roles.filter(name__in=['School Admin', 'HOD']).exists()

class ReportSettingsCreateView(SchoolAdminOrHODRequiredMixin, CreateView):
    model = ReportSettings
    template_name = 'reports/report_settings_form.html'
    fields = [
        'show_report_cover', 'show_subject_grades', 'show_student_remarks',
        'show_stream_rank', 'show_overall_rank', 'show_teacher_initials',
        'show_watermark', 'show_school_fees_layout', 'closing_date',
        'next_term_begins', 'class_teacher_remarks', 'principal_remarks'
    ]
    success_url = reverse_lazy('school_dashboard')
    
    def form_valid(self, form):
        form.instance.school = self.request.user.school
        return super().form_valid(form)

class ReportSettingsUpdateView(SchoolAdminOrHODRequiredMixin, UpdateView):
    model = ReportSettings
    template_name = 'reports/report_settings_form.html'
    fields = [
        'show_report_cover', 'show_subject_grades', 'show_student_remarks',
        'show_stream_rank', 'show_overall_rank', 'show_teacher_initials',
        'show_watermark', 'show_school_fees_layout', 'closing_date',
        'next_term_begins', 'class_teacher_remarks', 'principal_remarks'
    ]
    success_url = reverse_lazy('school_dashboard')

    def get_object(self, queryset=None):
        return get_object_or_404(ReportSettings, school=self.request.user.school)
