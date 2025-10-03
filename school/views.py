# Location: exam_system/school/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import CustomUser, Role, TeacherSubject, TeacherClass
from django.contrib import messages
from django.db.models import Q, Count, Avg, Max, Min
from .models import School, FormLevel, Stream
from .forms import UserCreationForm, FormLevelForm
from students.models import Student
from subjects.models import Subject, SubjectCategory
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
    from events.models import Event
    from datetime import datetime, timedelta
    import calendar as cal

    school = request.user.school

    # Get real statistics
    teacher_count = CustomUser.objects.filter(
        school=school,
        profile__roles__name='Teacher'
    ).distinct().count()

    # Calculate student count based on user role
    if request.user.is_superuser:
        # Admin sees all students in school
        student_count = Student.objects.filter(school=school).count()
    else:
        # Teachers see students taking their subjects
        teacher_subjects = TeacherSubject.objects.filter(teacher=request.user).values_list('subject', flat=True)
        student_count = Student.objects.filter(
            school=school,
            subjects__in=teacher_subjects
        ).distinct().count()

    # For now, staff count is 0 as we don't have a staff role yet
    staff_count = 0

    # Count unique streams
    stream_count = Student.objects.filter(school=school).values('stream').distinct().count()

    # Get calendar data for current month
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))

    # Create calendar
    cal_obj = cal.monthcalendar(year, month)
    month_name = cal.month_name[month]

    # Get events for this month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    events = Event.objects.filter(
        school=school,
        start_date__gte=start_date,
        start_date__lt=end_date
    )

    # Organize events by day
    events_by_day = {}
    for event in events:
        day = event.start_date.day
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)

    # Get high-level exam overview for dashboard
    recent_exams_count = Exam.objects.filter(
        school=school,
        is_active=True
    ).count()

    published_exams_count = Exam.objects.filter(
        school=school,
        is_active=True,
        is_published=True
    ).count()

    # Get overall school performance summary
    all_summaries = StudentExamSummary.objects.filter(
        exam__school=school,
        exam__is_active=True,
        exam__is_published=True
    )

    school_performance = {}
    if all_summaries.exists():
        school_performance = {
            'avg_points': round(all_summaries.aggregate(Avg('total_points'))['total_points__avg'] or 0, 2),
            'avg_marks': round(all_summaries.aggregate(Avg('mean_marks'))['mean_marks__avg'] or 0, 2),
            'total_exam_results': all_summaries.count(),
        }

    # Prepare exam data for template
    exam_data = {
        'recent_exams_count': recent_exams_count,
        'published_exams_count': published_exams_count,
        'school_performance': school_performance,
    }

    # Get billing information
    from billing.models import Subscription
    try:
        subscription = Subscription.objects.get(school=school)
        billing_info = {
            'subscription_type': subscription.subscription_type,
            'status': subscription.status,
            'end_date': subscription.end_date,
            'amount': subscription.amount,
        }
        # Calculate days remaining
        from datetime import date
        today = date.today()
        days_remaining = (subscription.end_date - today).days if subscription.end_date > today else 0
        billing_info['days_remaining'] = max(0, days_remaining)
        billing_info['next_payment'] = subscription.end_date.strftime('%b %d, %Y')
    except Subscription.DoesNotExist:
        billing_info = {
            'subscription_type': 'Not Set',
            'status': 'Inactive',
            'end_date': None,
            'amount': 0,
            'days_remaining': 0,
            'next_payment': 'N/A',
        }

    # Generate calendar days
    calendar_days = []
    for week in cal_obj:
        for day in week:
            if day != 0:
                is_today = (day == datetime.now().day and month == datetime.now().month and year == datetime.now().year)
                calendar_days.append({
                    'day': day,
                    'today': is_today,
                })
            else:
                calendar_days.append({
                    'day': '',
                    'today': False,
                })

    context = {
        'school': school,
        'teacher_count': teacher_count,
        'student_count': student_count,
        'staff_count': staff_count,
        'stream_count': stream_count,
        'calendar': cal_obj,
        'calendar_days': calendar_days,
        'year': year,
        'month': month,
        'month_name': month_name,
        'events_by_day': events_by_day,
        'today': datetime.now(),
        'exam_data': exam_data,
        'billing_info': billing_info,
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
def teacher_list(request):
    """
    Renders a list of all teachers in the school.
    """
    teachers = CustomUser.objects.filter(
        school=request.user.school,
        profile__roles__name='Teacher'
    ).select_related('profile').order_by('first_name', 'last_name')

    context = {
        'teachers': teachers,
        'total_teachers': teachers.count(),
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
    Shows form levels 1-4 as clickable cards.
    """
    school = request.user.school

    # Get form levels with student counts
    form_levels = []
    for form_level in range(1, 5):
        student_count = Student.objects.filter(school=school, form_level__number=form_level).count()
        stream_count = Student.objects.filter(school=school, form_level__number=form_level).values('stream').distinct().count()

        form_levels.append({
            'form_level': form_level,
            'student_count': student_count,
            'stream_count': stream_count,
        })

    context = {
        'form_levels': form_levels,
    }
    return render(request, 'school/forms_dashboard.html', context)

@login_required
def exam_management(request):
    """
    Placeholder view for exam creation and management.
    """
    return render(request, 'school/exam_management.html')

@login_required
def reports_and_analysis(request):
    """
    Exam analysis dashboard showing form levels for analysis selection.
    """
    school = request.user.school

    # Get form levels with exam data
    form_levels = []
    for form_level in range(1, 5):
        student_count = Student.objects.filter(school=school, form_level__number=form_level).count()
        exam_count = Exam.objects.filter(
            school=school,
            is_active=True,
            exam_results__student__form_level__number=form_level
        ).distinct().count()

        if exam_count > 0:
            form_levels.append({
                'form_level': form_level,
                'student_count': student_count,
                'exam_count': exam_count,
            })

    context = {
        'form_levels': form_levels,
    }
    return render(request, 'school/reports_and_analysis.html', context)

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
    Dashboard for a specific form level.
    Shows available streams for this form.
    """
    school = request.user.school

    # Get distinct streams for this form level
    streams = Student.objects.filter(
        school=school,
        form_level__number=form_level
    ).values_list('stream', flat=True).distinct().order_by('stream')

    # Get student count per stream
    stream_counts = {}
    total_students = 0
    for stream in streams:
        count = Student.objects.filter(
            school=school,
            form_level__number=form_level,
            stream=stream
        ).count()
        stream_counts[stream] = count
        total_students += count

    context = {
        'form_level': form_level,
        'streams': streams,
        'stream_counts': stream_counts,
        'total_students': total_students,
    }
    return render(request, 'school/class_dashboard.html', context)

@login_required
def stream_dashboard(request, form_level, stream):
    """
    Dashboard for a specific stream.
    Shows subject cards for result entry and a table with subject performance stats.
    """
    school = request.user.school

    # Get subjects available for this form
    subjects = Subject.objects.filter(
        school=school,
        is_active=True
    ).order_by('name')

    # Get subject performance data for cards and table
    subject_stats = []
    subject_performance_data = []

    for subject in subjects:
        # Get results for this subject and stream
        results = ExamResult.objects.filter(
            subject=subject,
            student__school=school,
            student__form_level__number=form_level,
            student__stream=stream,
            exam__is_active=True
        ).select_related('student', 'exam')

        if results.exists():
            avg_marks = results.aggregate(Avg('final_marks'))['final_marks__avg'] or 0
            max_marks = results.aggregate(Max('final_marks'))['final_marks__max'] or 0
            min_marks = results.aggregate(Min('final_marks'))['final_marks__min'] or 0
            total_marks = results.aggregate(Sum('final_marks'))['final_marks__sum'] or 0
            student_count = results.values('student').distinct().count()

            # Calculate average grade (simplified)
            avg_grade = 'E'  # Default
            if avg_marks >= 80:
                avg_grade = 'A'
            elif avg_marks >= 75:
                avg_grade = 'A-'
            elif avg_marks >= 70:
                avg_grade = 'B+'
            elif avg_marks >= 65:
                avg_grade = 'B'
            elif avg_marks >= 60:
                avg_grade = 'B-'
            elif avg_marks >= 55:
                avg_grade = 'C+'
            elif avg_marks >= 50:
                avg_grade = 'C'
            elif avg_marks >= 45:
                avg_grade = 'C-'
            elif avg_marks >= 40:
                avg_grade = 'D+'
            elif avg_marks >= 35:
                avg_grade = 'D'
            elif avg_marks >= 30:
                avg_grade = 'D-'

            subject_stats.append({
                'subject': subject,
                'avg_marks': round(avg_marks, 2),
                'student_count': student_count,
            })

            subject_performance_data.append({
                'subject': subject,
                'average_marks': round(avg_marks, 2),
                'total_marks': round(total_marks, 2),
                'max_marks': max_marks,
                'min_marks': min_marks,
                'average_grade': avg_grade,
                'student_count': student_count,
            })
        else:
            subject_stats.append({
                'subject': subject,
                'avg_marks': 0,
                'student_count': 0,
            })

            subject_performance_data.append({
                'subject': subject,
                'average_marks': 0,
                'total_marks': 0,
                'max_marks': 0,
                'min_marks': 0,
                'average_grade': '-',
                'student_count': 0,
            })

    context = {
        'form_level': form_level,
        'stream': stream,
        'subjects': subjects,
        'subject_stats': subject_stats,
        'subject_performance_data': subject_performance_data,
    }
    return render(request, 'school/stream_dashboard.html', context)

@login_required
def subject_dashboard(request, form_level=None, stream=None, subject_id=None):
    """
    Dashboard for a specific subject in a specific form/stream.
    If stream is None, shows streams for selection.
    If stream is provided, shows marks entry form for that stream.
    """
    school = request.user.school
    subject = get_object_or_404(Subject, id=subject_id, school=school)

    if stream is None:
        # Show streams for this form and subject
        streams = Student.objects.filter(
            school=school,
            form_level__number=form_level
        ).values_list('stream', flat=True).distinct().order_by('stream')

        context = {
            'subject': subject,
            'form_level': form_level,
            'streams': streams,
            'show_streams': True,
        }
        return render(request, 'school/subject_dashboard.html', context)
    else:
        # Show manual/auto entry choice for specific stream
        context = {
            'subject': subject,
            'form_level': form_level,
            'stream': stream,
            'show_entry_choice': True,
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
        avg_marks=Avg('final_marks'),
        max_marks=Max('final_marks'),
        student_count=Count('id')
    ).order_by('-avg_marks')[:10]

    # Recent exams
    recent_exams = Exam.objects.filter(
        is_active=True
    ).order_by('-created_at')[:10]

    context = {
        'stream_performance': stream_performance,
        'form_performance': form_performance,
        'subject_performance': subject_performance,
        'recent_exams': recent_exams,
    }
    return render(request, 'school/school_wide_dashboard.html', context)

@login_required
def department_dashboard(request, category_id):
    """
    Dashboard for a specific department (subject category).
    Shows analysis at form level, top students, deviations, graphs.
    """
    from subjects.models import SubjectCategory
    school = request.user.school
    category = get_object_or_404(SubjectCategory, id=category_id, school=school)

    # Get all subjects in this category
    subjects = Subject.objects.filter(category=category, school=school)

    # Get form-level performance for this department
    form_performance = []
    for form_level in range(1, 5):  # Forms 1-4
        students_in_form = Student.objects.filter(
            school=school,
            form_level__number=form_level
        )

        # Get exam results for subjects in this category
        results = ExamResult.objects.filter(
            subject__in=subjects,
            student__in=students_in_form,
            exam__is_active=True
        ).select_related('student', 'exam', 'subject')

        if results.exists():
            avg_marks = results.aggregate(Avg('final_marks'))['final_marks__avg'] or 0
            top_students = results.order_by('-final_marks')[:5]

            # Calculate deviations
            class_avg = avg_marks
            deviations = []
            for result in results.order_by('-exam__created_at')[:10]:
                deviation = result.final_marks - class_avg
                deviations.append({
                    'student': result.student,
                    'subject': result.subject,
                    'marks': result.final_marks,
                    'deviation': deviation,
                    'exam': result.exam
                })

            form_performance.append({
                'form_level': form_level,
                'student_count': students_in_form.count(),
                'avg_marks': round(avg_marks, 2),
                'top_students': top_students,
                'deviations': deviations[:5],  # Show top 5 deviations
                'subject_count': subjects.count()
            })

    # Get overall department statistics
    all_results = ExamResult.objects.filter(
        subject__in=subjects,
        exam__is_active=True,
        student__school=school
    )

    department_stats = {
        'total_students': Student.objects.filter(school=school).count(),
        'total_subjects': subjects.count(),
        'avg_performance': all_results.aggregate(Avg('final_marks'))['final_marks__avg'] or 0,
        'top_performers': all_results.values('student').annotate(
            avg_marks=Avg('final_marks')
        ).order_by('-avg_marks')[:10]
    }

    context = {
        'category': category,
        'subjects': subjects,
        'form_performance': form_performance,
        'department_stats': department_stats,
    }
    return render(request, 'school/department_dashboard.html', context)

@login_required
def subject_entry(request, form_level, stream, subject_id):
    """
    Show marks entry form for a specific subject, form, and stream.
    """
    from exams.models import GradingSystem
    school = request.user.school
    subject = get_object_or_404(Subject, id=subject_id, school=school)

    students = Student.objects.filter(
        school=school,
        form_level__number=form_level,
        stream=stream
    ).order_by('admission_number')

    # Get active exams for this form level
    exams = Exam.objects.filter(
        school=school,
        form_level=form_level,
        is_active=True
    ).order_by('-created_at')

    exam_id = request.GET.get('exam_id') or request.POST.get('exam_id')
    selected_exam = None
    exam_results = []
    exam_results_dict = {}

    if exam_id:
        try:
            selected_exam = Exam.objects.get(id=exam_id, school=school, is_active=True)
            # Get existing results for this exam, subject, and students
            exam_results = ExamResult.objects.filter(
                exam=selected_exam,
                subject=subject,
                student__in=students
            ).select_related('student', 'exam')
            exam_results_dict = {result.student.id: result for result in exam_results}
        except Exam.DoesNotExist:
            selected_exam = None
            exam_results = []
            exam_results_dict = {}

    if request.method == 'POST' and selected_exam:
        max_marks = float(request.POST.get('max_marks', 100))
        # Process marks submission
        for student in students:
            marks_key = f'marks_{student.id}'
            marks_value = request.POST.get(marks_key)
            if marks_value:
                try:
                    marks = float(marks_value)
                    # Convert to 100 scale if max_marks is different
                    if max_marks != 100:
                        marks = (marks / max_marks) * 100

                    # Get or create exam result
                    exam_result, created = ExamResult.objects.get_or_create(
                        exam=selected_exam,
                        student=student,
                        subject=subject,
                        defaults={'final_marks': marks, 'teacher': request.user}
                    )
                    if not created:
                        exam_result.final_marks = marks
                        exam_result.teacher = request.user

                    # Assign grade using grading system
                    grading_system = GradingSystem.objects.filter(
                        school=school,
                        is_active=True
                    ).first()  # Use default grading system

                    if grading_system:
                        grade, points = grading_system.get_grade_and_points(marks)
                        exam_result.grade = grade
                        exam_result.points = points

                    exam_result.save()

                except (ValueError, TypeError):
                    continue

        messages.success(request, 'Marks saved successfully!')
        return redirect(request.path + f'?exam_id={selected_exam.id}')

    context = {
        'subject': subject,
        'students': students,
        'exams': exams,
        'selected_exam': selected_exam,
        'exam_results': exam_results,
        'exam_results_dict': exam_results_dict,
        'form_level': form_level,
        'stream': stream,
    }
    return render(request, 'school/subject_entry.html', context)

@login_required
def departments_dashboard(request):
    """
    Dashboard showing all departments (subject categories) with teacher counts.
    """
    school = request.user.school

    categories = SubjectCategory.objects.filter(school=school)

    department_data = []
    for category in categories:
        teacher_count = TeacherSubject.objects.filter(
            subject__category=category,
            teacher__school=school
        ).values('teacher').distinct().count()

        department_data.append({
            'category': category,
            'teacher_count': teacher_count,
        })

    context = {
        'department_data': department_data,
    }
    return render(request, 'school/departments_dashboard.html', context)

@login_required

@login_required
def category_subjects(request, category_id):
    """
    Show subjects in a specific category.
    """
    school = request.user.school
    category = get_object_or_404(SubjectCategory, id=category_id, school=school)

    subjects = Subject.objects.filter(category=category, school=school, is_active=True)

    context = {
        'category': category,
        'subjects': subjects,
    }
    return render(request, 'school/category_subjects.html', context)

@login_required
def stream_students(request, form_level, stream):
    """
    Show students in a specific stream for management.
    """
    school = request.user.school

    students = Student.objects.filter(
        school=school,
        form_level__number=form_level,
        stream=stream
    ).order_by('admission_number')

    context = {
        'students': students,
        'form_level': form_level,
        'stream': stream,
    }
    return render(request, 'school/stream_students.html', context)

@login_required
def subject_teachers(request, subject_id):
    """
    Show teachers teaching a specific subject.
    """
    school = request.user.school
    subject = get_object_or_404(Subject, id=subject_id, school=school)

    teacher_assignments = TeacherSubject.objects.filter(subject=subject).select_related('teacher')
    teachers = [assignment.teacher for assignment in teacher_assignments]

    context = {
        'subject': subject,
        'teachers': teachers,
    }
    return render(request, 'school/subject_teachers.html', context)

@login_required
def add_teacher_to_subject(request, subject_id):
    """
    Add a teacher to a subject.
    """
    school = request.user.school
    subject = get_object_or_404(Subject, id=subject_id, school=school)

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        teacher = get_object_or_404(CustomUser, id=teacher_id, school=school, profile__roles__name='Teacher')

        # Check if already assigned
        if not TeacherSubject.objects.filter(teacher=teacher, subject=subject).exists():
            TeacherSubject.objects.create(teacher=teacher, subject=subject)
            messages.success(request, f'{teacher.get_full_name()} added to {subject.name}')
        else:
            messages.warning(request, f'{teacher.get_full_name()} is already assigned to {subject.name}')

        return redirect('school:subject_teachers', subject_id=subject.id)

    # Get teachers not already assigned to this subject
    assigned_teachers = TeacherSubject.objects.filter(subject=subject).values_list('teacher', flat=True)
    available_teachers = CustomUser.objects.filter(
        school=school,
        profile__roles__name='Teacher'
    ).exclude(id__in=assigned_teachers)

    context = {
        'subject': subject,
        'available_teachers': available_teachers,
    }
    return render(request, 'school/add_teacher_to_subject.html', context)

@login_required
def remove_teacher_from_subject(request, subject_id, teacher_id):
    """
    Remove a teacher from a subject.
    """
    school = request.user.school
    subject = get_object_or_404(Subject, id=subject_id, school=school)
    teacher = get_object_or_404(CustomUser, id=teacher_id, school=school)

    assignment = get_object_or_404(TeacherSubject, teacher=teacher, subject=subject)
    assignment.delete()
    messages.success(request, f'{teacher.get_full_name()} removed from {subject.name}')

    return redirect('school:subject_teachers', subject_id=subject.id)

@login_required
def exam_upload_subjects(request, form_level, exam_id, stream):
    """
    Exam upload - shows subject groups for the selected stream.
    """
    school = request.user.school
    exam = get_object_or_404(Exam, id=exam_id, school=school, is_active=True)

    # Get subject categories
    categories = SubjectCategory.objects.filter(school=school)

    category_data = []
    for category in categories:
        subject_count = Subject.objects.filter(
            category=category,
            school=school,
            is_active=True
        ).count()

        category_data.append({
            'category': category,
            'subject_count': subject_count,
        })

    context = {
        'exam': exam,
        'form_level': form_level,
        'stream': stream,
        'category_data': category_data,
    }
    return render(request, 'school/exam_upload_subjects.html', context)
@login_required
def exam_upload_streams(request, form_level, exam_id):
    """
    Exam upload - shows streams for the selected exam and form.
    """
    school = request.user.school
    exam = get_object_or_404(Exam, id=exam_id, school=school, is_active=True)

    # Get streams for this form
    streams = Student.objects.filter(
        school=school,
        form_level__number=form_level
    ).values_list('stream', flat=True).distinct().order_by('stream')

    stream_data = []
    for stream in streams:
        student_count = Student.objects.filter(
            school=school,
            form_level__number=form_level,
            stream=stream
        ).count()

        # Check completion for this stream
        existing_results = ExamResult.objects.filter(
            exam=exam,
            student__form_level__number=form_level,
            student__stream=stream,
            student__school=school
        ).count()

        completion_percentage = (existing_results / student_count * 100) if student_count > 0 else 0

        stream_data.append({
            'stream': stream,
            'student_count': student_count,
            'existing_results': existing_results,
            'completion_percentage': completion_percentage,
        })

    context = {
        'exam': exam,
        'form_level': form_level,
        'stream_data': stream_data,
    }
    return render(request, 'school/exam_upload_streams.html', context)
@login_required
def form_report_card(request, form_level):
    """
    Form-level report card generation - shows options for whole form or individual streams.
    """
    school = request.user.school

    # Get streams for this form
    streams = Student.objects.filter(
        school=school,
        form_level__number=form_level
    ).values_list('stream', flat=True).distinct().order_by('stream')

    # Get student count for whole form
    total_students = Student.objects.filter(school=school, form_level__number=form_level).count()

    context = {
        'form_level': form_level,
        'streams': streams,
        'total_students': total_students,
    }
    return render(request, 'school/form_report_card.html', context)

@login_required
def form_upload_exam(request, form_level):
    """
    Form-level exam upload - shows exams available for upload.
    """
    school = request.user.school

    # Get exams that have been created for this school
    exams = Exam.objects.filter(
        school=school,
        is_active=True
    ).order_by('-created_at')

    exam_data = []
    for exam in exams:
        # Check if results already exist for this form
        existing_results = ExamResult.objects.filter(
            exam=exam,
            student__form_level__number=form_level,
            student__school=school
        ).count()

        total_students = Student.objects.filter(
            school=school,
            form_level__number=form_level
        ).count()

        exam_data.append({
            'exam': exam,
            'existing_results': existing_results,
            'total_students': total_students,
            'completion_percentage': (existing_results / total_students * 100) if total_students > 0 else 0,
        })

    context = {
        'form_level': form_level,
        'exam_data': exam_data,
    }
    return render(request, 'school/form_upload_exam.html', context)
@login_required
def student_report_card(request):
    """
    Student Report Card generation - shows form levels for selection.
    """
    school = request.user.school

    # Get form levels with student counts
    form_levels = []
    for form_level in range(1, 5):
        student_count = Student.objects.filter(school=school, form_level__number=form_level).count()
        if student_count > 0:
            form_levels.append({
                'form_level': form_level,
                'student_count': student_count,
            })

    context = {
        'form_levels': form_levels,
    }
    return render(request, 'school/student_report_card.html', context)

@login_required
def upload_exam(request):
    """
    Upload Exam results - shows form levels for selection.
    """
    school = request.user.school

    # Get form levels with exam data
    form_levels = []
    for form_level in range(1, 5):
        student_count = Student.objects.filter(school=school, form_level__number=form_level).count()
        exam_count = Exam.objects.filter(
            school=school,
            is_active=True,
            exam_results__student__form_level__number=form_level
        ).distinct().count()

        if exam_count > 0:
            form_levels.append({
                'form_level': form_level,
                'student_count': student_count,
                'exam_count': exam_count,
            })

    context = {
        'form_levels': form_levels,
    }
    return render(request, 'school/upload_exam.html', context)
@login_required
def exam_merit_list(request, form_level, exam_id):
    """
    Show merit list for a specific exam and form level with subject cards.
    """
    school = request.user.school
    exam = get_object_or_404(Exam, id=exam_id, school=school, is_active=True)

    # Get student summaries for this exam and form
    summaries = StudentExamSummary.objects.filter(
        exam=exam,
        student__form_level__number=form_level,
        student__school=school
    ).select_related('student').order_by('-total_marks')

    # Get subjects for this exam
    subjects = Subject.objects.filter(
        school=school,
        is_active=True
    ).order_by('name')

    # Get subject performance data
    subject_performance = []
    for subject in subjects:
        results = ExamResult.objects.filter(
            exam=exam,
            subject=subject,
            student__form_level=form_level,
            student__school=school
        )

        if results.exists():
            avg_marks = results.aggregate(Avg('final_marks'))['final_marks__avg'] or 0
            max_marks = results.aggregate(Max('final_marks'))['final_marks__max'] or 0
            student_count = results.count()

            subject_performance.append({
                'subject': subject,
                'avg_marks': round(avg_marks, 2),
                'max_marks': max_marks,
                'student_count': student_count,
            })

    context = {
        'exam': exam,
        'form_level': form_level,
        'summaries': summaries,
        'subject_performance': subject_performance,
    }
    return render(request, 'school/exam_merit_list.html', context)
@login_required
def exam_form_analysis(request, form_level):
    """
    Show list of exams for a specific form level.
    """
    school = request.user.school

    # Get exams that have results for this form level
    exams = Exam.objects.filter(
        school=school,
        is_active=True,
        exam_results__student__form_level=form_level
    ).distinct().order_by('-created_at')

    exam_data = []
    for exam in exams:
        student_count = StudentExamSummary.objects.filter(
            exam=exam,
            student__form_level=form_level
        ).count()

        exam_data.append({
            'exam': exam,
            'student_count': student_count,
        })

    context = {
        'form_level': form_level,
        'exam_data': exam_data,
    }
    return render(request, 'school/exam_form_analysis.html', context)

@login_required
def teacher_detail(request, teacher_id):
    """
    Show detailed information about a specific teacher.
    """
    school = request.user.school
    teacher = get_object_or_404(CustomUser, id=teacher_id, school=school)

    # Get teacher's assigned classes
    assigned_classes = TeacherClass.objects.filter(teacher=teacher).order_by('form_level', 'stream')

    # Get subjects taught by this teacher
    taught_subjects = Subject.objects.filter(
        teacher_assignments__teacher=teacher
    ).distinct().order_by('name')

    # Get teacher statistics
    total_students = Student.objects.filter(
        subjects__teacher_assignments__teacher=teacher
    ).distinct().count()

    context = {
        'teacher': teacher,
        'assigned_classes': assigned_classes,
        'taught_subjects': taught_subjects,
        'total_students': total_students,
    }
    return render(request, 'school/teacher_detail.html', context)
    return render(request, 'school/subject_teachers.html', context)
