# Location: exam_system/school/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import School
from .forms import UserCreationForm
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# --- Class-Based Views for School Model Management ---

class SchoolDashboardView(LoginRequiredMixin, ListView):
    """
    This is a List View for the School model, not the main dashboard.
    It lists all schools (if multiple exist) for the superuser.
    """
    model = School
    template_name = 'school/school_dashboard.html'
    context_object_name = 'schools'

class SchoolCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = School
    template_name = 'school/school_form.html'
    fields = ['name', 'location', 'logo', 'address', 'phone_number', 'email']
    success_url = reverse_lazy('school:school_dashboard')

    def test_func(self):
        return self.request.user.is_superuser

class SchoolUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = School
    template_name = 'school/school_form.html'
    fields = ['name', 'location', 'logo', 'address', 'phone_number', 'email']
    success_url = reverse_lazy('school:school_dashboard')

    def test_func(self):
        return self.request.user.is_superuser

class SchoolDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = School
    template_name = 'school/school_confirm_delete.html'
    success_url = reverse_lazy('school:school_dashboard')

    def test_func(self):
        return self.request.user.is_superuser

# --- Function-Based Views for Dashboards & Roles ---

@login_required
def school_dashboard(request):
    """
    Renders the main school dashboard homepage (the one with the cards).
    This is the central navigation hub for the system.
    """
    return render(request, 'school/school_dashboard.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def principal_control(request):
    """
    Handles the Principal's control panel. Displays a form for creating new users
    and processes the form submission.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                # For now, we'll assign roles using is_staff, and add a custom profile model later.
                if role == 'teacher':
                    user.is_staff = True
                    user.save()
                    messages.success(request, f"Successfully created new teacher account for: {username}.")
                elif role == 'student':
                    messages.success(request, f"Successfully created new student account for: {username}.")
                return redirect('school:principal_control')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                logging.error(f"Error creating user: {e}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UserCreationForm()

    context = {
        'form': form
    }
    return render(request, 'school/principal_control.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def teacher_list(request):
    """
    Renders a list of all teachers.
    For now, we'll assume a teacher is any user with is_staff=True.
    A more robust solution with a dedicated Teacher model will be implemented later.
    """
    teachers = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('username')
    context = {
        'teachers': teachers
    }
    return render(request, 'school/teacher_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def student_list(request):
    """
    Renders a list of all students.
    For now, we will assume a student is any user that is not a staff member or superuser.
    A more robust solution with a dedicated Student model will be implemented later.
    """
    students = User.objects.filter(is_staff=False, is_superuser=False).order_by('username')
    context = {
        'students': students
    }
    return render(request, 'school/student_list.html', context)

@login_required
def forms_dashboard(request):
    """
    Placeholder view for the forms dashboard (Form 1, Form 2, etc.).
    """
    return render(request, 'school/forms_dashboard.html')

@login_required
def exam_management(request):
    """
    Placeholder view for exam creation and management.
    """
    return render(request, 'school/exam_management.html')

@login_required
def reports_and_analysis(request):
    """
    Placeholder view for generating reports and analyzing data.
    """
    return render(request, 'school/reports_and_analysis.html')
