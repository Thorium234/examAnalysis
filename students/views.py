from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import Student, StudentAdvancement
from .forms import StudentForm
from subjects.models import Subject

# Mixin to restrict views to school admins, HODs, and teachers
class SchoolAdminOrHODRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return user.profile.roles.filter(name__in=['School Admin', 'HOD', 'Teacher']).exists()

class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'form_levels'

    def get_queryset(self):
        # This view now shows form levels, not students
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school = self.request.user.school if not self.request.user.is_superuser else None

        # Get form levels with student counts
        form_levels = []
        for form_level in range(1, 5):
            if self.request.user.is_superuser:
                student_count = Student.objects.filter(form_level=form_level).count()
            else:
                student_count = Student.objects.filter(school=school, form_level=form_level).count()

            if student_count > 0:
                form_levels.append({
                    'form_level': form_level,
                    'student_count': student_count,
                })

        context['form_levels'] = form_levels
        return context

class StudentCreateView(SchoolAdminOrHODRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    success_url = reverse_lazy('students:student_list')
    
    def form_valid(self, form):
        if not self.request.user.school:
            messages.error(self.request, 'Your account is not associated with a school. Please contact an administrator.')
            return self.form_invalid(form)
        form.instance.school = self.request.user.school
        messages.success(self.request, f'Student {form.instance.name} created successfully.')
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
class StudentUpdateView(SchoolAdminOrHODRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')

    def form_valid(self, form):
        messages.success(self.request, f'Student {form.instance.name} updated successfully.')
        return super().form_valid(form)

    def get_queryset(self):
        return Student.objects.filter(school=self.request.user.school)

class StudentDeleteView(SchoolAdminOrHODRequiredMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('students:student_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, f'Student {self.get_object().name} deleted successfully.')
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Student.objects.filter(school=self.request.user.school)

class StudentSubjectEnrollmentView(SchoolAdminOrHODRequiredMixin, UpdateView):
    model = Student
    template_name = 'students/student_subject_enrollment.html'
    fields = ['subjects']
    success_url = reverse_lazy('students:student_list')

    def form_valid(self, form):
        messages.success(self.request, f'Subjects updated for {form.instance.name}.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_subjects'] = Subject.objects.filter(school=self.request.user.school).order_by('name')
        return context

class FormLevelDashboardView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'students/form_dashboard.html'
    context_object_name = 'students'

    def get_queryset(self):
        form_level = self.kwargs['form_level']
        if self.request.user.is_superuser:
            return Student.objects.filter(form_level=form_level).order_by('stream', 'name')
        return Student.objects.filter(
            school=self.request.user.school,
            form_level=form_level
        ).order_by('stream', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_level = self.kwargs['form_level']
        school = self.request.user.school if not self.request.user.is_superuser else None

        # Get streams for this form level
        if self.request.user.is_superuser:
            streams = Student.objects.filter(form_level=form_level).values_list('stream', flat=True).distinct().order_by('stream')
        else:
            streams = Student.objects.filter(school=school, form_level=form_level).values_list('stream', flat=True).distinct().order_by('stream')

        # Get student count per stream
        stream_data = []
        for stream in streams:
            if self.request.user.is_superuser:
                student_count = Student.objects.filter(form_level=form_level, stream=stream).count()
            else:
                student_count = Student.objects.filter(school=school, form_level=form_level, stream=stream).count()

            stream_data.append({
                'stream': stream,
                'student_count': student_count,
            })

        context['form_level'] = form_level
        context['stream_data'] = stream_data
        context['total_students'] = sum(s['student_count'] for s in stream_data)
        return context

class StreamStudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'students/stream_students.html'
    context_object_name = 'students'

    def get_queryset(self):
        form_level = self.kwargs['form_level']
        stream = self.kwargs['stream']
        if self.request.user.is_superuser:
            return Student.objects.filter(form_level=form_level, stream=stream).order_by('name')
        return Student.objects.filter(
            school=self.request.user.school,
            form_level=form_level,
            stream=stream
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_level = self.kwargs['form_level']
        stream = self.kwargs['stream']

        context['form_level'] = form_level
        context['stream'] = stream
        context['student_count'] = self.get_queryset().count()
        return context

# Views for Student Advancement
class StudentAdvancementCreateView(SchoolAdminOrHODRequiredMixin, CreateView):
    model = StudentAdvancement
    fields = ['student', 'from_form_level', 'to_form_level', 'advancement_year']
    template_name = 'students/advancement_form.html'
    success_url = reverse_lazy('students:student_list')

    def form_valid(self, form):
        form.instance.school = self.request.user.school
        messages.success(self.request, f'Advancement created for {form.instance.student.name}.')
        return super().form_valid(form)
