# Location: exam_system/school/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import CustomUser, Role
from django.contrib import messages
from django.db.models import Q, Count, Avg, Max, Min
from .models import School, FormLevel, Stream
from .forms import UserCreationForm, FormLevelForm
from students.models import Student
from subjects.models import Subject
from exams.models import Exam, ExamResult, StudentExamSummary
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

# --- Function-Based Views for School-Related Dashboards ---

@login_required
def school_dashboard(request):
    """
    Main dashboard for the school.
    """
    school = request.user.school
    context = {
        'school': school,
    }
    return render(request, 'school/school_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def principal_control(request):
    """
    Principal's control panel to manage user accounts.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                school=request.user.school
            )
            role_obj, _ = Role.objects.get_or_create(name=role)
            user.profile.roles.add(role_obj)
            messages.success(request, 'User created successfully!')
            return redirect('school:principal_control')
    else:
        form = UserCreationForm()

    context = {'form': form}
    return render(request, 'school/principal_control.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def teacher_list(request):
    """
    Renders a list of all teachers.
    For now, we'll assume a teacher is any user with is_staff=True.
    A more robust solution with a dedicated Teacher model will be implemented later.
    """
    teachers = CustomUser.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('username')
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
    students = CustomUser.objects.filter(is_staff=False, is_superuser=False).order_by('username')
    context = {
        'students': students
    }
    return render(request, 'school/student_list.html', context)

@login_required
def forms_dashboard(request):
    """
    Renders the dashboard for managing forms and classes.
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
    Placeholder view for reports and analysis.
    """
    return render(request, 'school/reports_and_analysis.html')

# --- FormLevel Views (New) ---

class FormLevelListView(LoginRequiredMixin, ListView):
    """
    Displays a list of all existing form levels.
    """
    model = FormLevel
    template_name = 'school/form_level_list.html'
    context_object_name = 'form_levels'

    def get_queryset(self):
        # Filter form levels by the user's school
        return FormLevel.objects.filter(school=self.request.user.school)


class FormLevelCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new form level.
    """
    model = FormLevel
    form_class = FormLevelForm
    template_name = 'school/form_level_form.html'
    success_url = reverse_lazy('school:forms_dashboard')

    def form_valid(self, form):
        # Automatically set the school to the current user's school
        form.instance.school = self.request.user.school
        return super().form_valid(form)

# --- New Dashboard Views ---

@login_required
def class_dashboard(request, form_level):
    """
    Dashboard for students from a specific form level only.
    Shows subject cards, student list with horizontal marks, and analysis.
    """
    school = request.user.school
    students = Student.objects.filter(
        school=school,
        form_level=form_level,
        is_active=True
    ).order_by('stream', 'admission_number')

    # Get subjects available for this form
    subjects = Subject.objects.filter(
        school=school,
        is_active=True
    ).order_by('name')

    # Get recent exams for this form
    exams = Exam.objects.filter(
        participating_forms=form_level,
        is_active=True
    ).order_by('-date_created')[:5]

    # Get subject performance data for cards
    subject_stats = []
    for subject in subjects:
        # Get top 3 students in this subject for recent exams
        recent_results = ExamResult.objects.filter(
            subject=subject,
            exam__participating_forms=form_level,
            exam__is_active=True
        ).select_related('student').order_by('-total_marks')[:3]

        subject_stats.append({
            'subject': subject,
            'top_students': recent_results,
            'avg_marks': recent_results.aggregate(Avg('total_marks'))['total_marks__avg'] or 0
        })

    context = {
        'form_level': form_level,
        'students': students,
        'subjects': subjects,
        'subject_stats': subject_stats,
        'exams': exams,
        'streams': students.values_list('stream', flat=True).distinct(),
    }
    return render(request, 'school/class_dashboard.html', context)

@login_required
def stream_dashboard(request, form_level, stream):
    """
    Dashboard for students from a specific stream only.
    Shows subject cards, student list with horizontal marks, and analysis.
    """
    school = request.user.school
    students = Student.objects.filter(
        school=school,
        form_level=form_level,
        stream=stream,
        is_active=True
    ).order_by('admission_number')

    # Get subjects available for this form
    subjects = Subject.objects.filter(
        school=school,
        is_active=True
    ).order_by('name')

    # Get recent exams for this form
    exams = Exam.objects.filter(
        participating_forms=form_level,
        is_active=True
    ).order_by('-date_created')[:5]

    # Get subject performance data for cards
    subject_stats = []
    for subject in subjects:
        # Get top 3 students in this subject for this stream
        recent_results = ExamResult.objects.filter(
            subject=subject,
            student__stream=stream,
            exam__participating_forms=form_level,
            exam__is_active=True
        ).select_related('student').order_by('-total_marks')[:3]

        subject_stats.append({
            'subject': subject,
            'top_students': recent_results,
            'avg_marks': recent_results.aggregate(Avg('total_marks'))['total_marks__avg'] or 0
        })

    context = {
        'form_level': form_level,
        'stream': stream,
        'students': students,
        'subjects': subjects,
        'subject_stats': subject_stats,
        'exams': exams,
    }
    return render(request, 'school/stream_dashboard.html', context)

@login_required
def subject_dashboard(request, form_level=None, stream=None, subject_id=None):
    """
    Dashboard for a specific subject in a specific form/stream.
    Shows marks entry form and student list for that subject.
    """
    school = request.user.school
    subject = get_object_or_404(Subject, id=subject_id, school=school)

    # Filter students based on form/stream
    students_query = Student.objects.filter(school=school, is_active=True)
    if form_level:
        students_query = students_query.filter(form_level=form_level)
    if stream:
        students_query = students_query.filter(stream=stream)

    students = students_query.order_by('admission_number')

    # Get recent exam results for this subject
    exam_results = ExamResult.objects.filter(
        subject=subject,
        student__in=students
    ).select_related('student', 'exam').order_by('-exam__date_created')[:20]

    context = {
        'subject': subject,
        'students': students,
        'exam_results': exam_results,
        'form_level': form_level,
        'stream': stream,
    }
    return render(request, 'school/subject_dashboard.html', context)

@login_required
def school_wide_dashboard(request):
    """
    School-wide dashboard showing top streams, forms, subjects, and overall analysis.
    """
    school = request.user.school

    # Top performing streams
    stream_performance = StudentExamSummary.objects.filter(
        exam__is_active=True,
        student__school=school
    ).values('student__stream').annotate(
        avg_total_marks=Avg('total_marks'),
        avg_mean_grade=Avg('mean_grade'),
        student_count=Count('id')
    ).order_by('-avg_total_marks')[:5]

    # Top performing forms
    form_performance = StudentExamSummary.objects.filter(
        exam__is_active=True,
        student__school=school
    ).values('student__form_level').annotate(
        avg_total_marks=Avg('total_marks'),
        avg_mean_grade=Avg('mean_grade'),
        student_count=Count('id')
    ).order_by('-avg_total_marks')[:4]

    # Top performing subjects
    subject_performance = ExamResult.objects.filter(
        exam__is_active=True,
        student__school=school
    ).values('subject__name').annotate(
        avg_marks=Avg('total_marks'),
        max_marks=Max('total_marks'),
        student_count=Count('id')
    ).order_by('-avg_marks')[:10]

    # Recent exams
    recent_exams = Exam.objects.filter(
        is_active=True
    ).order_by('-date_created')[:10]

    context = {
        'stream_performance': stream_performance,
        'form_performance': form_performance,
        'subject_performance': subject_performance,
        'recent_exams': recent_exams,
    }
    return render(request, 'school/school_wide_dashboard.html', context)