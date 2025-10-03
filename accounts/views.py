from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.core.mail import send_mail
from datetime import datetime
import random
import string
from .models import CustomUser, Profile, TeacherClass, Role
from school.models import School
from students.models import Student
from exams.models import ExamResult, Exam, GradingSystem, SubjectCategory, GradingRange
from subjects.models import Subject, SubjectPaper
from django.db.models import Count, Q, Avg, Max
from django.db.models import Count, Q, Avg
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
# Mixin to ensure a user is an admin (Principal or superuser)
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.request.user.profile.roles.filter(name='Principal').exists()


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

class CustomLogoutView(LogoutView):
    pass

class TeacherDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/teacher_dashboard.html'

    def get_context_data(self, **kwargs):
        # Always call the parent method to get the default context
        context = super().get_context_data(**kwargs)

        user = self.request.user
        school = user.school

        # Get teacher's assigned classes
        assigned_classes = TeacherClass.objects.filter(teacher=user).order_by('form_level', 'stream')

        # Get unique form levels assigned to this teacher
        assigned_forms = assigned_classes.values_list('form_level', flat=True).distinct().order_by('form_level')

        # Get subjects taught by this teacher
        taught_subjects = Subject.objects.filter(
            teacher_assignments__teacher=user
        ).distinct().order_by('name')

        # Get exam management data - exams where teacher has subjects
        teacher_exams = []
        for form_level in assigned_forms:
            streams_in_form = assigned_classes.filter(form_level=form_level).values_list('stream', flat=True).distinct()
            for stream in streams_in_form:
                subjects_in_stream = taught_subjects.filter(
                    teacher_assignments__teacher=user,
                    teacher_assignments__form_level=form_level,
                    teacher_assignments__stream=stream
                )

                for subject in subjects_in_stream:
                    # Get exams for this subject/form/stream
                    exams = Exam.objects.filter(
                        school=school,
                        exam_results__subject=subject,
                        exam_results__student__form_level=form_level,
                        exam_results__student__stream=stream
                    ).distinct().order_by('-created_at')

                    for exam in exams:
                        # Check completion status
                        total_students = Student.objects.filter(
                            school=school,
                            form_level=form_level,
                            stream=stream
                        ).count()

                        existing_results = ExamResult.objects.filter(
                            exam=exam,
                            subject=subject,
                            student__form_level=form_level,
                            student__stream=stream
                        ).count()

                        completion_percentage = (existing_results / total_students * 100) if total_students > 0 else 0

                        teacher_exams.append({
                            'exam': exam,
                            'form_level': form_level,
                            'stream': stream,
                            'subject': subject,
                            'total_students': total_students,
                            'existing_results': existing_results,
                            'completion_percentage': completion_percentage,
                            'status': 'Published' if exam.is_published else 'Draft',
                        })

        # Add the data to the context dictionary
        context.update({
            'assigned_forms': assigned_forms,
            'assigned_classes': assigned_classes,
            'taught_subjects': taught_subjects,
            'teacher_exams': teacher_exams,
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


# Multi-step Authentication Views
class FindAccountView(TemplateView):
    template_name = 'accounts/find_account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_hour = datetime.now().hour

        if 5 <= current_hour < 12:
            greeting = "Good morning"
        elif 12 <= current_hour < 17:
            greeting = "Good afternoon"
        elif 17 <= current_hour < 21:
            greeting = "Good evening"
        else:
            greeting = "Hello"

        context['greeting'] = greeting
        return context

    def post(self, request, *args, **kwargs):
        username_or_email = request.POST.get('username_or_email', '').strip()

        if not username_or_email:
            messages.error(request, 'Please enter your username or email address.')
            return redirect('accounts:find_account')

        # Try to find user by username or email
        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                messages.error(request, 'Account not found. Please check your username or email address.')
                return redirect('accounts:find_account')

        # Store user ID in session for next step
        request.session['pending_user_id'] = user.id
        return redirect('accounts:account_found')


class AccountFoundView(TemplateView):
    template_name = 'accounts/account_found.html'

    def get(self, request, *args, **kwargs):
        user_id = request.session.get('pending_user_id')
        if not user_id:
            return redirect('accounts:find_account')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect('accounts:find_account')

        context = self.get_context_data(**kwargs)
        context['user'] = user
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        user_id = request.session.get('pending_user_id')
        if not user_id:
            return redirect('accounts:find_account')

        password = request.POST.get('password')
        if not password:
            messages.error(request, 'Please enter your password.')
            return redirect('accounts:account_found')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect('accounts:find_account')

        # Authenticate user
        user_auth = authenticate(request, username=user.username, password=password)
        if user_auth is not None:
            login(request, user_auth)
            # Clear session
            if 'pending_user_id' in request.session:
                del request.session['pending_user_id']
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            messages.error(request, 'Incorrect password. Please try again.')
            return redirect('accounts:account_found')


class GoodbyeView(TemplateView):
    template_name = 'accounts/goodbye.html'


class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get school users (excluding current user)
        school_users = User.objects.filter(school=user.school).exclude(id=user.id).select_related('profile')

        context.update({
            'school_users': school_users,
            'school_info': user.school,
        })
        return context


class ChangePasswordView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/change_password.html'

    def post(self, request, *args, **kwargs):
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('accounts:change_password')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('accounts:change_password')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('accounts:change_password')

        request.user.set_password(new_password)
        request.user.save()
        messages.success(request, 'Password changed successfully.')
        return redirect('accounts:profile')


class PasswordResetRequestView(TemplateView):
    template_name = 'accounts/password_reset_request.html'

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip()

        if not email:
            messages.error(request, 'Please enter your email address.')
            return redirect('accounts:password_reset_request')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return redirect('accounts:password_reset_request')

        # Generate reset code
        reset_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        request.session['reset_code'] = reset_code
        request.session['reset_user_id'] = user.id

        # Send email (in real implementation, use proper email service)
        try:
            send_mail(
                'Password Reset Code',
                f'Your password reset code is: {reset_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Reset code sent to your email.')
        except:
            messages.error(request, 'Failed to send email. Please try again.')

        return redirect('accounts:password_reset_confirm')


class PasswordResetConfirmView(TemplateView):
    template_name = 'accounts/password_reset_confirm.html'

    def post(self, request, *args, **kwargs):
        reset_code = request.POST.get('reset_code')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        session_code = request.session.get('reset_code')
        user_id = request.session.get('reset_user_id')

        if not all([reset_code, new_password, confirm_password, session_code, user_id]):
            messages.error(request, 'Invalid reset attempt.')
            return redirect('accounts:find_account')

        if reset_code != session_code:
            messages.error(request, 'Invalid reset code.')
            return redirect('accounts:password_reset_confirm')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('accounts:password_reset_confirm')

        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()

            # Clear session
            del request.session['reset_code']
            del request.session['reset_user_id']

            messages.success(request, 'Password reset successfully. You can now log in.')
            return redirect('accounts:find_account')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('accounts:find_account')


# Student Authentication Views
class StudentLoginView(TemplateView):
    template_name = 'accounts/student_login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_hour = datetime.now().hour

        if 5 <= current_hour < 12:
            greeting = "Good morning"
        elif 12 <= current_hour < 17:
            greeting = "Good afternoon"
        elif 17 <= current_hour < 21:
            greeting = "Good evening"
        else:
            greeting = "Hello"

        context['greeting'] = greeting
        return context

    def post(self, request, *args, **kwargs):
        school_code = request.POST.get('school_code', '').strip().upper()
        admission_number = request.POST.get('admission_number', '').strip().upper()

        if not school_code or not admission_number:
            messages.error(request, 'Please enter both school code and admission number.')
            return redirect('accounts:student_login')

        # Authenticate using our custom backend
        user = authenticate(request, school_code=school_code, admission_number=admission_number)

        if user is not None:
            login(request, user)
            # Store student info in session for dashboard
            try:
                student = Student.objects.get(
                    school__school_code=school_code,
                    admission_number=admission_number
                )
                request.session['student_id'] = student.id
                request.session['student_authenticated'] = True
            except Student.DoesNotExist:
                pass

            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            messages.error(request, 'Invalid school code or admission number. Please try again.')
            return redirect('accounts:student_login')


class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/student_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Check if user is a student
        if not user.profile.roles.filter(name='Student').exists():
            return redirect('accounts:teacher_dashboard')

        # Get student information
        student_id = self.request.session.get('student_id')
        if student_id:
            try:
                student = Student.objects.get(id=student_id, school=user.school)
                context['student'] = student

                # Get student's exam results and summaries
                from exams.models import StudentExamSummary, ExamResult
                exam_summaries = StudentExamSummary.objects.filter(
                    student=student
                ).select_related('exam').order_by('-exam__year', '-exam__term')

                context['exam_summaries'] = exam_summaries

                # Get recent exam results
                recent_results = ExamResult.objects.filter(
                    student=student
                ).select_related('exam', 'subject').order_by('-exam__year', '-exam__term')[:10]

            except Student.DoesNotExist:
                messages.error(self.request, 'Student information not found.')
                return redirect('accounts:student_login')

        return context
# Admin Dashboard Views
class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'accounts/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        school = user.school

        # Get all school users with their profiles and roles
        school_users = User.objects.filter(school=school).select_related('profile').prefetch_related('profile__roles')

        # Prepare user data with roles
        users_data = []
        for user_obj in school_users:
            roles = list(user_obj.profile.roles.all()) if hasattr(user_obj, 'profile') else []
            role_names = [role.name for role in roles]

            # Get additional info for teachers
            teacher_classes = []
            teacher_subjects = []
            if 'Teacher' in role_names or 'Class Teacher' in role_names:
                teacher_classes = TeacherClass.objects.filter(teacher=user_obj).select_related('school')
                teacher_subjects = Subject.objects.filter(teacher_assignments__teacher=user_obj).distinct()

            users_data.append({
                'user': user_obj,
                'roles': roles,
                'role_names': role_names,
                'teacher_classes': teacher_classes,
                'teacher_subjects': teacher_subjects,
            })

        # Get all available roles
        all_roles = Role.objects.all().order_by('name')

        context.update({
            'school_users': users_data,
            'school_info': school,
            'total_users': len(users_data),
            'all_roles': all_roles,
        })
        return context
# Teacher Navigation Views
@login_required
def teacher_form_streams(request, form_level):
    """
    Show streams for a specific form that the teacher is assigned to.
    """
    user = request.user
    school = user.school

    # Check if teacher is assigned to this form
    assigned_classes = TeacherClass.objects.filter(
        teacher=user,
        form_level=form_level
    )

    if not assigned_classes.exists():
        messages.error(request, 'You are not assigned to this form.')
        return redirect('accounts:teacher_dashboard')

    # Get unique streams for this form that teacher is assigned to
    streams = assigned_classes.values_list('stream', flat=True).distinct().order_by('stream')

    context = {
        'form_level': form_level,
        'streams': streams,
    }
    return render(request, 'accounts/teacher_form_streams.html', context)

@login_required
def teacher_stream_subjects(request, form_level, stream):
    """
    Show subjects for a specific stream/form that the teacher teaches.
    """
    user = request.user
    school = user.school

    # Check if teacher is assigned to this form/stream
    if not TeacherClass.objects.filter(
        teacher=user,
        form_level=form_level,
        stream=stream
    ).exists():
        messages.error(request, 'You are not assigned to this form/stream.')
        return redirect('accounts:teacher_dashboard')

    # Get subjects taught by this teacher in this form/stream
    subjects = Subject.objects.filter(
        teacher_assignments__teacher=user,
        teacher_assignments__form_level=form_level,
        teacher_assignments__stream=stream
    ).distinct().order_by('name')

    context = {
        'form_level': form_level,
        'stream': stream,
        'subjects': subjects,
    }
    return render(request, 'accounts/teacher_stream_subjects.html', context)

@login_required
def teacher_subject_students(request, form_level, stream, subject_id):
    """
    Show students and exam options for a specific subject/stream/form.
    """
    user = request.user
    school = user.school
    subject = get_object_or_404(Subject, id=subject_id, school=school)

    # Check if teacher teaches this subject in this form/stream
    if not TeacherSubject.objects.filter(
        teacher=user,
        subject=subject,
        form_level=form_level,
        stream=stream
    ).exists():
        messages.error(request, 'You do not teach this subject in this form/stream.')
        return redirect('accounts:teacher_dashboard')

    # Get students in this form/stream
    students = Student.objects.filter(
        school=school,
        form_level=form_level,
        stream=stream
    ).order_by('admission_number')

    # Get exams for this subject/form/stream
    exams = Exam.objects.filter(
        school=school,
        exam_results__subject=subject,
        exam_results__student__form_level=form_level,
        exam_results__student__stream=stream
    ).distinct().order_by('-created_at')

    # Get exam data with analytics
    exam_data = []
    for exam in exams:
        # Get results for this exam/subject/stream
        results = ExamResult.objects.filter(
            exam=exam,
            subject=subject,
            student__form_level=form_level,
            student__stream=stream
        )

        if results.exists():
            avg_marks = results.aggregate(Avg('final_marks'))['final_marks__avg'] or 0
            max_marks = results.aggregate(Max('final_marks'))['final_marks__max'] or 0
            min_marks = results.aggregate(Min('final_marks'))['final_marks__min'] or 0
            student_count = results.count()

            exam_data.append({
                'exam': exam,
                'avg_marks': round(avg_marks, 2),
                'max_marks': max_marks,
                'min_marks': min_marks,
                'student_count': student_count,
                'mean_points': round(avg_marks / 10, 2) if avg_marks else 0,  # Assuming 10-point scale
                'mean_grade': 'A' if avg_marks >= 80 else 'B' if avg_marks >= 70 else 'C' if avg_marks >= 60 else 'D' if avg_marks >= 50 else 'E',
            })

    context = {
        'form_level': form_level,
        'stream': stream,
        'subject': subject,
        'students': students,
        'exam_data': exam_data,
    }
    return render(request, 'accounts/teacher_subject_students.html', context)

# Admin API Views for managing users
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

@method_decorator(csrf_exempt, name='dispatch')
class UserDetailAPIView(AdminRequiredMixin, View):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, school=request.user.school)
            roles = list(user.profile.roles.values_list('id', flat=True))
            return JsonResponse({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'get_full_name': user.get_full_name(),
                },
                'roles': roles,
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class ManageUserAPIView(AdminRequiredMixin, View):
    def post(self, request):
        user_id = request.POST.get('user_id')
        role_ids = request.POST.getlist('roles[]')
        form_level = request.POST.get('form_level')
        stream = request.POST.get('stream')
        is_class_teacher = request.POST.get('is_class_teacher') == 'on'

        try:
            user = User.objects.get(id=user_id, school=request.user.school)
            profile = user.profile

            # Update roles
            profile.roles.clear()
            for role_id in role_ids:
                try:
                    role = Role.objects.get(id=role_id)
                    profile.roles.add(role)
                except Role.DoesNotExist:
                    pass

            # Handle teacher-specific assignments
            if 'Teacher' in [role.name for role in profile.roles.all()]:
                # Create or update teacher class assignment
                if form_level and stream:
                    TeacherClass.objects.get_or_create(
                        teacher=user,
                        school=user.school,
                        form_level=int(form_level),
                        stream=stream,
                        defaults={'is_class_teacher': is_class_teacher}
                    )

            profile.save()
            return JsonResponse({'success': True, 'message': 'User roles updated successfully'})

        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)