from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import CustomUser, Profile, TeacherClass, Role
from school.models import School
from students.models import Student
from exams.models import ExamResult, Exam, GradingSystem, SubjectCategory, GradingRange
from subjects.models import Subject, SubjectPaper
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden

User = get_user_model()

# Mixin to ensure only a teacher can access a view
class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.request.user.profile.roles.filter(name='Teacher').exists()

# Mixin to ensure a user is an HOD
class HODRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.profile.roles.filter(name='HOD').exists()

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

class TeacherDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/teacher_dashboard.html'

    def get_context_data(self, **kwargs):
        # Always call the parent method to get the default context
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        school = user.school
        
        # Get total number of exams, students, and subjects for the current school
        total_exams = Exam.objects.filter(school=school).count()
        total_students = Student.objects.filter(school=school).count()
        total_subjects = Subject.objects.filter(school=school).count()
        
        # Get streams and their student counts
        streams = Student.objects.filter(school=school).values('form_level', 'stream').annotate(student_count=Count('stream')).order_by('form_level', 'stream')

        # Add the data to the context dictionary
        context.update({
            'total_exams': total_exams,
            'total_students': total_students,
            'total_subjects': total_subjects,
            'streams': streams,
        })
        return context

class ProfileCreateView(LoginRequiredMixin, CreateView):
    model = Profile
    fields = ['roles', 'phone_number']
    template_name = 'accounts/profile_form.html'
    success_url = reverse_lazy('teacher_dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ['roles', 'phone_number']
    template_name = 'accounts/profile_form.html'
    success_url = reverse_lazy('teacher_dashboard')

    def get_object(self, queryset=None):
        return self.request.user.profile

# LoginRequiredMixin is redundant here because TeacherRequiredMixin already inherits from it.
class TeacherClassCreateView(TeacherRequiredMixin, CreateView):
    model = TeacherClass
    fields = ['teacher', 'form_level', 'stream', 'is_class_teacher']
    template_name = 'accounts/teacher_class_form.html'
    success_url = reverse_lazy('teacher_dashboard')
 
# LoginRequiredMixin is redundant here
class TeacherClassUpdateView(TeacherRequiredMixin, UpdateView):
    model = TeacherClass
    fields = ['teacher', 'form_level', 'stream', 'is_class_teacher']
    template_name = 'accounts/teacher_class_form.html'
    success_url = reverse_lazy('teacher_dashboard')

# LoginRequiredMixin is redundant here
class TeacherClassDeleteView(TeacherRequiredMixin, DeleteView):
    model = TeacherClass
    template_name = 'accounts/teacher_class_confirm_delete.html'
    success_url = reverse_lazy('teacher_dashboard')
