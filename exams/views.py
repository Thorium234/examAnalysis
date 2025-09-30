from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db.models import Count, Avg, Min, Max, F, Prefetch
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, TemplateView, DetailView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.db import transaction

import csv
from io import TextIOWrapper

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from students.models import Student
from subjects.models import Subject, SubjectPaper, SubjectPaperRatio
from school.models import School # This is the corrected import
from .models import (
    Exam,
    ExamResult,
    StudentExamSummary,
    SubjectCategory,
    GradingSystem,
    GradingRange,
    PaperResult
)
from .forms import GradingSystemForm, GradingRangeForm, SubjectPaperRatioForm

# Mixins for permissions
class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.profile.roles.filter(name='Teacher').exists()

class HODRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.profile.roles.filter(name='HOD').exists()


# Exam CRUD Views
#----------------------------------------------------------------------
class ExamCreateView(TeacherRequiredMixin, CreateView):
    model = Exam
    fields = ['name', 'form_level', 'year', 'term', 'participating_forms', 'is_ordinary_exam', 'is_consolidated_exam', 'is_kcse', 'is_year_average', 'is_active']
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exam_list')

    def form_valid(self, form):
        if not self.request.user.school:
            form.add_error(None, "You must be associated with a school to create an exam.")
            return self.form_invalid(form)
        form.instance.school = self.request.user.school
        return super().form_valid(form)

class ExamUpdateView(TeacherRequiredMixin, UpdateView):
    model = Exam
    fields = ['name', 'form_level', 'year', 'term', 'participating_forms', 'is_ordinary_exam', 'is_consolidated_exam', 'is_kcse', 'is_year_average', 'is_active']
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exam_list')

class ExamDeleteView(TeacherRequiredMixin, DeleteView):
    model = Exam
    template_name = 'exams/exam_confirm_delete.html'
    success_url = reverse_lazy('exam_list')

class ExamListView(TeacherRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Exam.objects.all().order_by('-year', '-term')
        return Exam.objects.filter(school=self.request.user.school).order_by('-year', '-term')
# New hierarchical navigation views for result entry
@login_required
def exam_form_levels(request):
    """List form levels that have exams available for result entry"""
    if request.user.is_superuser:
        exams = Exam.objects.filter(is_active=True).order_by('-year', '-term')
    else:
        exams = Exam.objects.filter(school=request.user.school, is_active=True).order_by('-year', '-term')

    # Group exams by form level
    form_levels = {}
    for exam in exams:
        if exam.form_level not in form_levels:
            form_levels[exam.form_level] = []
        form_levels[exam.form_level].append(exam)

    context = {
        'form_levels': form_levels,
    }
    return render(request, 'exams/exam_form_levels.html', context)
@login_required
def exam_form_subjects(request, form_level):
    """List subjects for a specific form level that have exams available for result entry"""
    if request.user.is_superuser:
        exams = Exam.objects.filter(form_level=form_level, is_active=True).order_by('-year', '-term')
    else:
        exams = Exam.objects.filter(school=request.user.school, form_level=form_level, is_active=True).order_by('-year', '-term')

    # Get subjects that are taught in this form level
    subjects = Subject.objects.filter(
        form_levels=form_level,
        school=request.user.school if not request.user.is_superuser else None
    ).distinct().order_by('name')

    # Filter subjects based on teacher's assignments if not superuser
    if not request.user.is_superuser:
        # Get subjects assigned to this teacher
        from accounts.models import TeacherSubject
        teacher_subjects = TeacherSubject.objects.filter(
            teacher=request.user,
            form_level=form_level
        ).values_list('subject', flat=True)
        subjects = subjects.filter(id__in=teacher_subjects)

    context = {
        'form_level': form_level,
        'subjects': subjects,
        'exams': exams,
    }
    return render(request, 'exams/exam_form_subjects.html', context)
    context = {
        'form_level': form_level,}
    
@login_required
def exam_subject_results_entry(request, form_level, subject_id):
    """Improved result entry view that categorizes students by streams"""
    subject = get_object_or_404(Subject, pk=subject_id)

    # Check if teacher is assigned to this subject and form level
    if not request.user.is_superuser:
        from accounts.models import TeacherSubject
        if not TeacherSubject.objects.filter(teacher=request.user, subject=subject).exists():
            messages.error(request, "You are not assigned to teach this subject.")
            return redirect('exam_form_subjects', form_level=form_level)

    # Get students in this form level, grouped by stream
    students_by_stream = {}
    streams = Student.objects.filter(
        school=request.user.school if not request.user.is_superuser else None,
        form_level=form_level
    ).values_list('stream', flat=True).distinct().order_by('stream')

    for stream in streams:
        students = Student.objects.filter(
            school=request.user.school if not request.user.is_superuser else None,
            form_level=form_level,
            stream=stream,
            studentsubjectenrollment__subject=subject,
            studentsubjectenrollment__is_enrolled=True
        ).exclude(
            # Exclude students who already have results for this subject in active exams
            paperresult__exam__is_active=True,
            paperresult__subject_paper__subject=subject
        ).distinct().order_by('admission_number')

        if students.exists():
            students_by_stream[stream] = students

    # Get active exams for this form level
    exams = Exam.objects.filter(
        form_level=form_level,
        is_active=True,
        school=request.user.school if not request.user.is_superuser else None
    ).order_by('-year', '-term')

    context = {
        'form_level': form_level,
        'subject': subject,
        'students_by_stream': students_by_stream,
        'exams': exams,
    }

    if request.method == 'POST':
        return handle_bulk_result_entry(request, form_level, subject_id)

    return render(request, 'exams/exam_subject_results_entry.html', context)

@transaction.atomic
def handle_bulk_result_entry(request, form_level, subject_id):
    """Handle bulk result entry for a subject"""
    subject = get_object_or_404(Subject, pk=subject_id)
    exam_id = request.POST.get('exam')
    exam = get_object_or_404(Exam, pk=exam_id)

    success_count = 0
    error_count = 0

    # Process each student's marks
    for key, value in request.POST.items():
        if key.startswith('marks_'):
            parts = key.split('_')
            if len(parts) == 3:
                student_id = parts[1]
                status_key = f'status_{student_id}'

                marks_str = value.strip()
                status = request.POST.get(status_key, 'P')

                try:
                    student = Student.objects.get(pk=student_id)

                    # Validate marks
                    if status == 'P' and marks_str:
                        marks = float(marks_str)
                        if marks < 0 or marks > 100:
                            error_count += 1
                            continue
                    elif status in ['A', 'D']:
                        marks = None
                    else:
                        marks = float(marks_str) if marks_str else None

                    # Get or create subject paper (assuming single paper for simplicity)
                    paper, created = SubjectPaper.objects.get_or_create(
                        subject=subject,
                        name='Paper 1',
                        defaults={'paper_number': 1, 'max_marks': 100}
                    )

                    # Save result
                    PaperResult.objects.update_or_create(
                        exam=exam,
                        student=student,
                        subject_paper=paper,
                        defaults={
                            'marks': marks,
                            'status': status,
                            'entered_by': request.user
                        }
                    )

                    success_count += 1

                except (ValueError, Student.DoesNotExist):
                    error_count += 1
                    continue

    if success_count > 0:
        messages.success(request, f"Successfully saved {success_count} results.")
    if error_count > 0:
        messages.error(request, f"Failed to save {error_count} results due to errors.")

    return redirect('exam_subject_results_entry', form_level=form_level, subject_id=subject_id)

class GradingSystemCreateView(TeacherRequiredMixin, CreateView):
    model = GradingSystem
    form_class = GradingSystemForm
    template_name = 'exams/gradingsystem_form.html'
    success_url = reverse_lazy('exams:gradingsystem_list')

    def form_valid(self, form):
        if not self.request.user.school:
            form.add_error(None, "You must be associated with a school to create a grading system.")
            return self.form_invalid(form)
        form.instance.school = self.request.user.school
        return super().form_valid(form)

class GradingSystemListView(TeacherRequiredMixin, ListView):
    model = GradingSystem
    template_name = 'exams/gradingsystem_list.html'
    context_object_name = 'grading_systems'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return GradingSystem.objects.all().order_by('name')
        return GradingSystem.objects.filter(school=self.request.user.school).order_by('name')

class GradingSystemDetailView(TeacherRequiredMixin, DetailView):
    model = GradingSystem
    template_name = 'exams/gradingsystem_detail.html'
    context_object_name = 'grading_system'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return GradingSystem.objects.all()
        return GradingSystem.objects.filter(school=self.request.user.school)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grading_system = self.object
        context['grading_ranges'] = GradingRange.objects.filter(grading_system=grading_system).order_by('-min_marks')
        return context

class GradingSystemUpdateView(TeacherRequiredMixin, UpdateView):
    model = GradingSystem
    form_class = GradingSystemForm
    template_name = 'exams/gradingsystem_form.html'
    success_url = reverse_lazy('exams:gradingsystem_list')

    def get_queryset(self):
        if self.request.user.is_superuser:
            return GradingSystem.objects.all()
        return GradingSystem.objects.filter(school=self.request.user.school)

class GradingSystemDeleteView(TeacherRequiredMixin, DeleteView):
    model = GradingSystem
    template_name = 'exams/gradingsystem_confirm_delete.html'
    success_url = reverse_lazy('exams:gradingsystem_list')

    def get_queryset(self):
        if self.request.user.is_superuser:
            return GradingSystem.objects.all()
        return GradingSystem.objects.filter(school=self.request.user.school)

class GradingRangeCreateView(TeacherRequiredMixin, CreateView):
    model = GradingRange
    form_class = GradingRangeForm
    template_name = 'exams/gradingrange_form.html'
    success_url = reverse_lazy('exams:gradingsystem_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grading_system_pk'] = self.kwargs['grading_system_pk']
        return context

    def form_valid(self, form):
        grading_system = get_object_or_404(GradingSystem, pk=self.kwargs['grading_system_pk'])
        form.instance.grading_system = grading_system
        return super().form_valid(form)

class GradingRangeUpdateView(TeacherRequiredMixin, UpdateView):
    model = GradingRange
    form_class = GradingRangeForm
    template_name = 'exams/gradingrange_form.html'
    success_url = reverse_lazy('exams:gradingsystem_list')

class GradingRangeDeleteView(TeacherRequiredMixin, DeleteView):
    model = GradingRange
    template_name = 'exams/gradingrange_confirm_delete.html'
    success_url = reverse_lazy('exams:gradingsystem_list')

class SubjectPaperRatioListView(TeacherRequiredMixin, ListView):
    model = Subject
    template_name = 'exams/subject_paper_ratio_list.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Subject.objects.all().select_related('paper_ratio').order_by('name')
        return Subject.objects.filter(school=self.request.user.school).select_related('paper_ratio').order_by('name')

class SubjectPaperRatioCreateView(TeacherRequiredMixin, CreateView):
    model = SubjectPaperRatio
    form_class = SubjectPaperRatioForm
    template_name = 'exams/subject_paper_ratio_form.html'
    success_url = reverse_lazy('exams:paper_ratios_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        subject_id = self.request.GET.get('subject')
        if subject_id:
            try:
                subject = Subject.objects.get(pk=subject_id)
                if self.request.user.is_superuser or subject.school == self.request.user.school:
                    initial['subject'] = subject
            except Subject.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        if not self.request.user.school and not self.request.user.is_superuser:
            form.add_error(None, "You must be associated with a school to create paper ratios.")
            return self.form_invalid(form)
        return super().form_valid(form)

class SubjectPaperRatioUpdateView(TeacherRequiredMixin, UpdateView):
    model = SubjectPaperRatio
    form_class = SubjectPaperRatioForm
    template_name = 'exams/subject_paper_ratio_form.html'
    success_url = reverse_lazy('exams:paper_ratios_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        if self.request.user.is_superuser:
            return SubjectPaperRatio.objects.all()
        return SubjectPaperRatio.objects.filter(subject__school=self.request.user.school)

class SubjectPaperRatioDeleteView(TeacherRequiredMixin, DeleteView):
    model = SubjectPaperRatio
    template_name = 'exams/subject_paper_ratio_confirm_delete.html'
    success_url = reverse_lazy('exams:paper_ratios_list')

    def get_queryset(self):
        if self.request.user.is_superuser:
            return SubjectPaperRatio.objects.all()
        return SubjectPaperRatio.objects.filter(subject__school=self.request.user.school)

# Exam Results Upload Choice View
#----------------------------------------------------------------------
@login_required
@permission_required('exams.add_examresult', raise_exception=True)
def exam_results_upload_choice(request, pk):
    if request.user.is_superuser:
        exam = get_object_or_404(Exam, pk=pk)
    else:
        exam = get_object_or_404(Exam, pk=pk, school=request.user.school)

    context = {
        'exam': exam,
    }

    return render(request, 'exams/upload_results_choice.html', context)
# Subject Results View
#----------------------------------------------------------------------
@login_required
@permission_required('exams.view_examresult', raise_exception=True)
def subject_results(request, exam_pk, subject_pk):
    if request.user.is_superuser:
        exam = get_object_or_404(Exam, pk=exam_pk)
    else:
        exam = get_object_or_404(Exam, pk=exam_pk, school=request.user.school)
    subject = get_object_or_404(Subject, pk=subject_pk)

    # Get all results for this subject and exam
    subject_results = ExamResult.objects.filter(
        exam=exam,
        subject=subject
    ).select_related('student').order_by('-final_marks')

    # Calculate subject statistics
    if subject_results.exists():
        marks_list = [r.final_marks for r in subject_results]
        subject_stats = {
            'highest_marks': max(marks_list),
            'lowest_marks': min(marks_list),
            'mean_marks': sum(marks_list) / len(marks_list),
            'total_students': len(subject_results)
        }

        # Assign subject ranks
        rank = 1
        prev_marks = None
        for result in subject_results:
            if result.final_marks != prev_marks:
                result.subject_rank = rank
                prev_marks = result.final_marks
            else:
                result.subject_rank = rank
            rank += 1
            result.save()
    else:
        subject_stats = {
            'highest_marks': 0,
            'lowest_marks': 0,
            'mean_marks': 0,
            'total_students': 0
        }

    context = {
        'exam': exam,
        'subject': subject,
        'subject_results': subject_results,
        'subject_stats': subject_stats,
    }
# Stream Results View
#----------------------------------------------------------------------
@login_required
@permission_required('exams.view_examresult', raise_exception=True)
def stream_results(request, exam_pk, form_level, stream):
    if request.user.is_superuser:
        exam = get_object_or_404(Exam, pk=exam_pk)
    else:
        exam = get_object_or_404(Exam, pk=exam_pk, school=request.user.school)

    # Get students in this stream
    students = Student.objects.filter(
        school=request.user.school,
        form_level=form_level,
        stream=stream
    ).order_by('admission_number')

    # Get subjects for this form level
    subjects = Subject.objects.filter(
        form_levels=form_level,
        school=request.user.school
    ).order_by('name')

    # Get exam summaries for these students
    stream_results = StudentExamSummary.objects.filter(
        exam=exam,
        student__in=students
    ).select_related('student').order_by('stream_position')

    # Calculate stream statistics
    if stream_results.exists():
        totals = [r.total_marks for r in stream_results]
        points = [r.total_points for r in stream_results]
        grades = [r.mean_grade for r in stream_results]

        stream_stats = {
            'highest_total': max(totals) if totals else 0,
            'lowest_total': min(totals) if totals else 0,
            'mean_total': sum(totals) / len(totals) if totals else 0,
            'mean_points': sum(points) / len(points) if points else 0,
            'mean_grade': max(set(grades), key=grades.count) if grades else 'N/A',  # Most common grade
        }
    else:
        stream_stats = {
            'highest_total': 0,
            'lowest_total': 0,
            'mean_total': 0,
            'mean_points': 0,
            'mean_grade': 'N/A',
        }

    # Get subject results for each student
    for result in stream_results:
        subject_results = {}
        exam_results = ExamResult.objects.filter(
            exam=exam,
            student=result.student
        ).select_related('subject')
        for exam_result in exam_results:
            subject_results[exam_result.subject.id] = exam_result
        result.subject_results = subject_results

    # Get class teacher
    from accounts.models import TeacherClass
    class_teacher = None
    try:
        teacher_class = TeacherClass.objects.filter(
            form_level=form_level,
            stream=stream,
            is_class_teacher=True
        ).first()
        if teacher_class:
            class_teacher = teacher_class.teacher
    except:
        pass

    context = {
        'exam': exam,
        'form_level': form_level,
        'stream': stream,
        'stream_results': stream_results,
        'stream_stats': stream_stats,
        'subjects': subjects,
        'class_teacher': class_teacher,
    }

    return render(request, 'exams/stream_results.html', context)




# Exam Results Entry and Management
#----------------------------------------------------------------------

# Exam Results Entry and Management
#----------------------------------------------------------------------
@login_required
@permission_required('exams.add_examresult', raise_exception=True)
def exam_results_entry(request, pk):
    if request.user.is_superuser:
        exam = get_object_or_404(Exam, pk=pk)
    else:
        exam = get_object_or_404(Exam, pk=pk, school=request.user.school)
    students = Student.objects.filter(
        school=request.user.school,
        form_level__in=exam.participating_forms.all()
    ).order_by('stream', 'admission_number')

    subjects = Subject.objects.filter(
        form_levels__in=exam.participating_forms.all(),
        school=request.user.school
    ).prefetch_related('papers')

    context = {
        'exam': exam,
        'students': students,
        'subjects': subjects,
    }

    if request.method == 'POST':
        with transaction.atomic():
            try:
                student_id = request.POST.get('student')
                subject_id = request.POST.get('subject')

                if not student_id or not subject_id:
                    messages.error(request, "Please select both student and subject.")
                    return redirect('exam_results_entry', pk=pk)

                student = get_object_or_404(Student, pk=student_id, school=request.user.school)
                subject = get_object_or_404(Subject, pk=subject_id)

                # Process paper data
                paper_index = 0
                while f'paper_{paper_index}_marks' in request.POST:
                    marks_str = request.POST.get(f'paper_{paper_index}_marks', '')
                    ratio_str = request.POST.get(f'paper_{paper_index}_ratio', '')
                    paper_name = request.POST.get(f'paper_{paper_index}_name', '')

                    if marks_str and ratio_str:
                        marks = int(marks_str)
                        ratio = int(ratio_str)

                        # Get or create the subject paper
                        paper, created = SubjectPaper.objects.get_or_create(
                            subject=subject,
                            name=paper_name,
                            defaults={'paper_number': paper_index + 1, 'max_marks': 100}
                        )

                        # Save paper result
                        PaperResult.objects.update_or_create(
                            exam=exam,
                            student=student,
                            subject_paper=paper,
                            defaults={
                                'marks': marks,
                                'status': 'P'  # Present
                            }
                        )

                        # Update or create subject paper ratio
                        SubjectPaperRatio.objects.update_or_create(
                            subject=subject,
                            paper=paper,
                            defaults={'contribution_percentage': ratio}
                        )

                    paper_index += 1

                messages.success(request, f"Results saved successfully for {student.name} in {subject.name}.")
                return redirect('exam_results_entry', pk=pk)

            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                return redirect('exam_results_entry', pk=pk)

    return render(request, 'exams/enter_results.html', context)

# Download Exam Results Template View
#----------------------------------------------------------------------
@login_required
@permission_required('exams.add_examresult', raise_exception=True)
def download_exam_results_template(request, pk):
    if request.user.is_superuser:
        exam = get_object_or_404(Exam, pk=pk)
    else:
        exam = get_object_or_404(Exam, pk=pk, school=request.user.school)

    # Get all students for this exam
    students = Student.objects.filter(
        school=request.user.school,
        form_level__in=exam.participating_forms.all()
    ).order_by('admission_number')

    # Get all subjects for this exam
    subjects = Subject.objects.filter(
        school=request.user.school,
        form_levels__in=exam.participating_forms.all()
    ).order_by('name')

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{exam.name}_results_template.csv"'

    writer = csv.writer(response)
    writer.writerow(['admission_number', 'student_name', 'subject_name', 'marks', 'status'])

    # Write sample data for each student-subject combination
    for student in students:
        for subject in subjects:
            writer.writerow([
                student.admission_number,
                student.name,
                subject.name,
                '',  # Empty marks
                'P'  # Default to Present
            ])

    return response

# Upload Results View
#----------------------------------------------------------------------
@login_required
@permission_required('exams.add_examresult', raise_exception=True)
def upload_results(request, pk):
    if request.user.is_superuser:
        exam = get_object_or_404(Exam, pk=pk)
    else:
        exam = get_object_or_404(Exam, pk=pk, school=request.user.school)

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('exams:exam_results_upload_choice', pk=pk)

        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(decoded_file.splitlines())

            success_count = 0
            error_count = 0

            for row in csv_reader:
                try:
                    admission_number = row.get('admission_number', '').strip()
                    subject_name = row.get('subject_name', '').strip()
                    marks_str = row.get('marks', '').strip()
                    status = row.get('status', 'P').strip().upper()

                    if not admission_number or not subject_name:
                        error_count += 1
                        continue

                    # Get student
                    try:
                        student = Student.objects.get(
                            admission_number=admission_number,
                            school=request.user.school
                        )
                    except Student.DoesNotExist:
                        error_count += 1
                        continue

                    # Get subject
                    try:
                        subject = Subject.objects.get(
                            name=subject_name,
                            school=request.user.school
                        )
                    except Subject.DoesNotExist:
                        error_count += 1
                        continue

                    # Process marks
                    if status == 'P' and marks_str:
                        try:
                            marks = float(marks_str)
                        except ValueError:
                            error_count += 1
                            continue
                    else:
                        marks = None

                    # Create or update ExamResult
                    ExamResult.objects.update_or_create(
                        exam=exam,
                        student=student,
                        subject=subject,
                        defaults={
                            'final_marks': marks,
                            'status': status
                        }
                    )

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    continue

            messages.success(request, f'Successfully uploaded {success_count} results. {error_count} errors.')

        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')

        return redirect('exams:exam_results_summary', pk=pk)

    return render(request, 'exams/upload_results.html', {'exam': exam})

# Exam Results Summary View
#----------------------------------------------------------------------
@login_required
@permission_required('exams.view_examresult', raise_exception=True)
def exam_results_summary(request, pk):
    if request.user.is_superuser:
        exam = get_object_or_404(Exam, pk=pk)
    else:
        exam = get_object_or_404(Exam, pk=pk, school=request.user.school)

    # Get summary statistics
    total_students = Student.objects.filter(
        school=request.user.school,
        form_level__in=exam.participating_forms.all()
    ).count()

    total_results = ExamResult.objects.filter(exam=exam).count()

    subjects = Subject.objects.filter(
        school=request.user.school,
        form_levels__in=exam.participating_forms.all()
    )

    subject_summaries = []
    for subject in subjects:
        results = ExamResult.objects.filter(exam=exam, subject=subject)
        if results.exists():
            avg_marks = results.filter(final_marks__isnull=False).aggregate(Avg('final_marks'))['final_marks__avg']
            subject_summaries.append({
                'subject': subject,
                'total_entries': results.count(),
                'average_marks': round(avg_marks, 2) if avg_marks else 0,
                'highest_marks': results.filter(final_marks__isnull=False).aggregate(Max('final_marks'))['final_marks__max'] or 0,
                'lowest_marks': results.filter(final_marks__isnull=False).aggregate(Min('final_marks'))['final_marks__min'] or 0,
            })

    context = {
        'exam': exam,
        'total_students': total_students,
        'total_results': total_results,
        'subject_summaries': subject_summaries,
    }

    return render(request, 'exams/exam_summary_report.html', context)