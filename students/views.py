from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Student, StudentAdvancement
from subjects.models import Subject

# Mixin to restrict views to school admins and HODs
class SchoolAdminOrHODRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return user.profile.roles.filter(name__in=['School Admin', 'HOD']).exists()

class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Student.objects.all().order_by('school', 'form_level', 'stream', 'name')
        return Student.objects.filter(school=self.request.user.school).order_by('form_level', 'stream', 'name')

class StudentCreateView(SchoolAdminOrHODRequiredMixin, CreateView):
    model = Student
    template_name = 'students/student_form.html'
    fields = ['name', 'admission_number', 'kcpe_marks', 'stream', 'form_level', 'phone_contact']
    success_url = reverse_lazy('student_list')
    
    def form_valid(self, form):
        if not self.request.user.school:
            from django.contrib import messages
            messages.error(self.request, 'Your account is not associated with a school. Please contact an administrator.')
            return self.form_invalid(form)
        form.instance.school = self.request.user.school
        return super().form_valid(form)

class StudentUpdateView(SchoolAdminOrHODRequiredMixin, UpdateView):
    model = Student
    template_name = 'students/student_form.html'
    fields = ['name', 'admission_number', 'kcpe_marks', 'stream', 'form_level', 'phone_contact']
    success_url = reverse_lazy('student_list')
    
    def get_queryset(self):
        return Student.objects.filter(school=self.request.user.school)

class StudentDeleteView(SchoolAdminOrHODRequiredMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('student_list')
    
    def get_queryset(self):
        return Student.objects.filter(school=self.request.user.school)

class StudentSubjectEnrollmentView(SchoolAdminOrHODRequiredMixin, UpdateView):
    model = Student
    template_name = 'students/student_subject_enrollment.html'
    fields = ['subjects']
    success_url = reverse_lazy('student_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_subjects'] = Subject.objects.filter(school=self.request.user.school).order_by('name')
        return context

# Views for Student Advancement
class StudentAdvancementCreateView(SchoolAdminOrHODRequiredMixin, CreateView):
    model = StudentAdvancement
    fields = ['student', 'from_form_level', 'to_form_level', 'advancement_year']
    template_name = 'students/advancement_form.html'
    success_url = reverse_lazy('student_list')
    
    def form_valid(self, form):
        form.instance.school = self.request.user.school
        return super().form_valid(form)
