from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count, Avg, F
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, FormView
from django.views.generic.base import TemplateView
from .models import Student, StudentSubjectEnrollment

from .forms import StudentAdvancementForm, StudentAdvancementBulkUploadForm
from .models import Student, Subject, StudentAdvancement
from .utils.advancement import process_advancement_spreadsheet, generate_advancement_template
from exams.models import Exam, ExamResult, StudentExamSummary

@login_required
def dashboard(request):
    # Get some basic statistics for the dashboard
    total_students = Student.objects.filter(is_active=True).count()
    form_counts = Student.objects.filter(is_active=True).values('form_level').annotate(count=Count('id'))
    recent_exams = Exam.objects.filter(is_active=True).order_by('-date_created')[:5]
    
    context = {
        'total_students': total_students,
        'form_counts': form_counts,
        'recent_exams': recent_exams,
    }
    return render(request, 'students/dashboard.html', context)

@login_required
def student_list(request):
    students = Student.objects.filter(is_active=True).order_by('form_level', 'stream', 'name')
    
    # Filter by form and stream if provided
    form_level = request.GET.get('form_level')
    stream = request.GET.get('stream')
    search = request.GET.get('search')
    
    if form_level:
        students = students.filter(form_level=form_level)
    if stream:
        students = students.filter(stream=stream)
    if search:
        students = students.filter(
            Q(name__icontains=search) | 
            Q(admission_number__icontains=search)
        )
    
    context = {
        'students': students,
        'form_levels': [1, 2, 3, 4],
        'streams': ['East', 'West', 'North', 'South'],
        'selected_form': form_level,
        'selected_stream': stream,
        'search_query': search,
    }
    return render(request, 'students/student_list.html', context)

@login_required
def student_detail(request, admission_number):
    student = get_object_or_404(Student, admission_number=admission_number)
    exam_results = ExamResult.objects.filter(student=student).order_by('-exam__date_created')
    exam_summaries = StudentExamSummary.objects.filter(student=student).order_by('-exam__date_created')
    
    context = {
        'student': student,
        'exam_results': exam_results,
        'exam_summaries': exam_summaries,
    }
    return render(request, 'students/student_detail.html', context)

@login_required
def merit_list(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Filter by form level and stream if provided
    form_level = request.GET.get('form_level')
    stream = request.GET.get('stream')
    
    summaries = StudentExamSummary.objects.filter(exam=exam)
    
    if form_level:
        summaries = summaries.filter(student__form_level=form_level)
    
    if stream:
        # Get summaries for specific stream, ordered by pre-computed stream position
        summaries = summaries.filter(student__stream=stream).order_by('stream_position')
    else:
        # Get all summaries ordered by pre-computed overall position
        summaries = summaries.order_by('overall_position')
    
    # Get subject performance statistics
    subject_stats = ExamResult.objects.filter(
        exam=exam
    ).values('subject__name').annotate(
        avg_marks=Avg('total_marks'),
        count=Count('id')
    ).order_by('-avg_marks')
    
    context = {
        'exam': exam,
        'summaries': summaries,
        'subject_stats': subject_stats,
        'selected_form': form_level,
        'selected_stream': stream,
        'form_levels': [1, 2, 3, 4],
        'streams': ['East', 'West', 'North', 'South'],
    }
    return render(request, 'students/merit_list.html', context)

@login_required
def student_performance_graph(request, admission_number):
    student = get_object_or_404(Student, admission_number=admission_number)
    
    # Get all exams this student has participated in
    exam_results = ExamResult.objects.filter(
        student=student
    ).select_related(
        'exam', 'subject'
    ).order_by('exam__date_created', 'subject__name')
    
    # Organize data for graphing
    exams_data = {}
    for result in exam_results:
        exam_name = f"{result.exam.name} ({result.exam.year} Term {result.exam.term})"
        if exam_name not in exams_data:
            exams_data[exam_name] = {}
        exams_data[exam_name][result.subject.name] = result.total_marks
    
    context = {
        'student': student,
        'exams_data': exams_data,
    }
    return render(request, 'students/performance_graph.html', context)

@login_required
def student_report_card(request, admission_number, exam_id):
    student = get_object_or_404(Student, admission_number=admission_number)
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Get all results for this student in this exam
    results = ExamResult.objects.filter(
        student=student,
        exam=exam
    ).select_related('subject').order_by('subject__name')
    
    # Get summary
    summary = get_object_or_404(StudentExamSummary, student=student, exam=exam)
    
    context = {
        'student': student,
        'exam': exam,
        'results': results,
        'summary': summary,
    }
    return render(request, 'students/report_card.html', context)

@login_required
@permission_required('students.change_student')
def bulk_student_advancement(request):
    form_level = request.GET.get('form_level')
    stream = request.GET.get('stream')
    action = request.POST.get('action')
    
    students = Student.objects.filter(active=True)
    if form_level:
        students = students.filter(form_level=form_level)
    if stream:
        students = students.filter(stream=stream)
    
    if request.method == 'POST' and action:
        selected_students = request.POST.getlist('selected_students')
        if action == 'advance_form':
            # Move students to next form level
            students.filter(
                admission_number__in=selected_students,
                form_level__lt=4  # Don't advance beyond Form 4
            ).update(form_level=F('form_level') + 1)
            messages.success(request, f'Advanced {len(selected_students)} students to next form level')
            
        elif action == 'change_stream':
            new_stream = request.POST.get('new_stream')
            if new_stream:
                students.filter(
                    admission_number__in=selected_students
                ).update(stream=new_stream)
                messages.success(request, f'Changed stream for {len(selected_students)} students to {new_stream}')
                
        elif action == 'graduate':
            # Mark selected Form 4 students as graduated
            students.filter(
                admission_number__in=selected_students,
                form_level=4
            ).update(active=False, date_graduated=timezone.now())
            messages.success(request, f'Marked {len(selected_students)} Form 4 students as graduated')
    
    context = {
        'students': students.order_by('form_level', 'stream', 'admission_number'),
        'selected_form': form_level,
        'selected_stream': stream,
        'form_levels': [1, 2, 3, 4],
        'streams': ['East', 'West', 'North', 'South'],
    }
    return render(request, 'students/bulk_advancement.html', context)

class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    template_name = 'students/student_form.html'
    fields = ['admission_number', 'name', 'form_level', 'stream', 'kcpe_marks', 'phone_contact']
    success_url = reverse_lazy('students:student_list')

    def form_valid(self, form):
        messages.success(self.request, 'Student created successfully.')
        return super().form_valid(form)

class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    template_name = 'students/student_form.html'
    fields = ['name', 'form_level', 'stream', 'kcpe_marks', 'phone_contact', 'is_active']
    context_object_name = 'student'
    slug_field = 'admission_number'
    slug_url_kwarg = 'admission_number'

    def get_success_url(self):
        return reverse_lazy('students:student_detail', kwargs={'admission_number': self.object.admission_number})

    def form_valid(self, form):
        messages.success(self.request, 'Student information updated successfully.')
        return super().form_valid(form)

class StudentSubjectEnrollmentView(LoginRequiredMixin, UpdateView):
    model = Student
    template_name = 'students/student_subject_enrollment.html'
    fields = []
    context_object_name = 'student'
    slug_field = 'admission_number'
    slug_url_kwarg = 'admission_number'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        available_subjects = StudentSubjectEnrollment.get_available_subjects(student)
        current_enrollments = student.subject_enrollments.filter(is_enrolled=True).values_list('subject_id', flat=True)
        
        context['available_subjects'] = available_subjects
        context['current_enrollments'] = current_enrollments
        return context

    def post(self, request, *args, **kwargs):
        student = self.get_object()
        selected_subjects = request.POST.getlist('subjects')
        
        # Update enrollments
        StudentSubjectEnrollment.objects.filter(student=student).update(is_enrolled=False)
        for subject_id in selected_subjects:
            enrollment, created = StudentSubjectEnrollment.objects.get_or_create(
                student=student,
                subject_id=subject_id,
                defaults={'is_enrolled': True, 'modified_by': request.user}
            )
            if not created:
                enrollment.is_enrolled = True
                enrollment.modified_by = request.user
                enrollment.save()
        
        messages.success(request, 'Subject enrollments updated successfully.')
        return redirect('students:student_detail', admission_number=student.admission_number)

class StudentAdvancementListView(LoginRequiredMixin, ListView):
    model = StudentAdvancement
    template_name = 'students/advancement_list.html'
    context_object_name = 'advancements'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        form_level = self.request.GET.get('form_level')
        stream = self.request.GET.get('stream')
        academic_year = self.request.GET.get('year')
        
        if form_level:
            queryset = queryset.filter(current_form=form_level)
        if stream:
            queryset = queryset.filter(current_stream=stream)
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
            
        return queryset.select_related('student', 'created_by')
    ordering = ['-academic_year', 'current_form', 'current_stream']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        academic_year = self.request.GET.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academic_years'] = StudentAdvancement.objects.values_list(
            'academic_year', flat=True).distinct().order_by('-academic_year')
        return context

class StudentAdvancementCreateView(LoginRequiredMixin, CreateView):
    model = StudentAdvancement
    form_class = StudentAdvancementForm
    template_name = 'students/advancement_form.html'
    success_url = reverse_lazy('student-advancement-list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Student advancement record created successfully.')
        return response

class StudentAdvancementBulkUploadView(LoginRequiredMixin, FormView):
    form_class = StudentAdvancementBulkUploadForm
    template_name = 'students/advancement_bulk_upload.html'
    success_url = reverse_lazy('student-advancement-list')
    
    def form_valid(self, form):
        try:
            result = process_advancement_spreadsheet(
                self.request.FILES['excel_file'],
                form.cleaned_data['academic_year'],
                self.request.user
            )
            
            if result['success']:
                messages.success(
                    self.request,
                    f"Successfully processed {result['records_processed']} records."
                )
            else:
                messages.warning(
                    self.request,
                    f"Processed {result['records_processed']} records with {len(result['errors'])} errors."
                )
                for error in result['errors']:
                    messages.error(self.request, error)
                    
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class DownloadAdvancementTemplateView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        try:
            excel_file = generate_advancement_template()
            response = HttpResponse(
                excel_file,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=student_advancement_template.xlsx'
            return response
        except Exception as e:
            messages.error(request, f"Error generating template: {str(e)}")
            return redirect('student-advancement-list')