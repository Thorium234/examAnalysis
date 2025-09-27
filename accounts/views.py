from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.conf import settings
from datetime import datetime
import random
import string
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
    success_url = reverse_lazy('teacher_dashboard')
