from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db.models import Count, Avg, Min, Max, F
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Exam, ExamResult, StudentExamSummary
from students.models import Student, Subject
from .services import calculate_exam_statistics, process_results_upload
from django.db import transaction
import csv
from io import TextIOWrapper

class ExamCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Exam
    fields = ['name', 'year', 'term', 'form_level', 'exam_type']
    template_name = 'exams/exam_form.html'
    permission_required = 'exams.add_exam'
    success_url = reverse_lazy('exams:exam_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Exam created successfully.')
        return super().form_valid(form)

class ExamUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Exam
    fields = ['name', 'year', 'term', 'form_level', 'exam_type', 'is_active']
    template_name = 'exams/exam_form.html'
    permission_required = 'exams.change_exam'
    
    def get_success_url(self):
        return reverse_lazy('exams:exam_detail', kwargs={'exam_id': self.object.id})

    def form_valid(self, form):
        messages.success(self.request, 'Exam updated successfully.') 
        return super().form_valid(form)

class ExamDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Exam
    template_name = 'exams/exam_confirm_delete.html'
    permission_required = 'exams.delete_exam'
    success_url = reverse_lazy('exams:exam_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Exam deleted successfully.')
        return super().delete(request, *args, **kwargs)

@login_required
def exam_list(request):
    exams = Exam.objects.filter(is_active=True).order_by('-year', '-term', '-date_created')
    
    # Filter by form level and year if provided
    form_level = request.GET.get('form_level')
    year = request.GET.get('year')
    term = request.GET.get('term')
    
    if form_level:
        exams = exams.filter(form_level=form_level)
    if year:
        exams = exams.filter(year=year)
    if term:
        exams = exams.filter(term=term)
    
    # Get unique years for filter
    years = Exam.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    context = {
        'exams': exams,
        'form_levels': [1, 2, 3, 4],
        'years': years,
        'terms': [1, 2, 3],
        'selected_form': form_level,
        'selected_year': year,
        'selected_term': term,
    }
    return render(request, 'exams/exam_list.html', context)

@login_required
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Get exam statistics
    stats = calculate_exam_statistics(exam)
    
    # Get performance by stream
    stream_stats = StudentExamSummary.objects.filter(
        exam=exam
    ).values('student__stream').annotate(
        avg_total=Avg('total_marks'),
        min_total=Min('total_marks'),
        max_total=Max('total_marks'),
        student_count=Count('id')
    ).order_by('-avg_total')
    
    # Get subject performance
    subject_stats = ExamResult.objects.filter(
        exam=exam
    ).values('subject__name').annotate(
        avg_marks=Avg('total_marks'),
        min_marks=Min('total_marks'),
        max_marks=Max('total_marks'),
        student_count=Count('id')
    ).order_by('-avg_marks')
    
    # Get top performers using pre-computed overall position
    top_performers = StudentExamSummary.objects.filter(exam=exam).order_by('overall_position')[:10]
    
    context = {
        'exam': exam,
        'stats': stats,
        'stream_stats': stream_stats,
        'subject_stats': subject_stats,
        'top_performers': top_performers,
        'results': results,
        'subjects': subjects,
        'streams': streams,
        'selected_student': student_id,
        'selected_subject': subject_id,
        'selected_stream': stream,
    }
    return render(request, 'exams/exam_results.html', context)

@login_required
@permission_required('exams.change_examresult')
def edit_result(request, exam_id, result_id):
    result = get_object_or_404(ExamResult, id=result_id, exam_id=exam_id)
    
    if request.method == 'POST':
        try:
            new_marks = float(request.POST.get('marks', 0))
            if 0 <= new_marks <= 100:
                result.total_marks = new_marks
                result.calculate_grade()
                result.save()
                messages.success(request, 'Result updated successfully.')
            else:
                messages.error(request, 'Marks must be between 0 and 100.')
        except ValueError:
            messages.error(request, 'Invalid marks value.')
        
    return redirect('exams:exam_results', exam_id=exam_id)

@login_required
@permission_required('exams.add_examresult')
def add_result(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        marks = request.POST.get('marks')
        
        try:
            marks = float(marks)
            if 0 <= marks <= 100:
                result, created = ExamResult.objects.update_or_create(
                    exam=exam,
                    student_id=student_id,
                    subject_id=subject_id,
                    defaults={'total_marks': marks}
                )
                result.calculate_grade()
                result.save()
                messages.success(request, 'Result added successfully.')
            else:
                messages.error(request, 'Marks must be between 0 and 100.')
        except ValueError:
            messages.error(request, 'Invalid marks value.')
            
    return redirect('exams:exam_results', exam_id=exam_id)

@login_required
def download_results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{exam.name}_results.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Admission Number', 'Student Name', 'Subject', 'Marks', 'Grade', 'Class Position', 'Stream Position'])
    
    results = ExamResult.objects.filter(exam=exam).select_related(
        'student', 'subject'
    ).order_by('student__admission_number', 'subject__name')
    
    for result in results:
        summary = StudentExamSummary.objects.filter(
            exam=exam, 
            student=result.student
        ).first()
        
        writer.writerow([
            result.student.admission_number,
            result.student.full_name,
            result.subject.name,
            result.total_marks,
            result.get_grade(),
            summary.overall_position if summary else 'N/A',
            summary.stream_position if summary else 'N/A'
        ])
    
    return response

@login_required
def subject_analysis(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Get detailed subject statistics
    subject_stats = ExamResult.objects.filter(
        exam=exam
    ).values(
        'subject__name'
    ).annotate(
        avg_marks=Avg('total_marks'),
        max_marks=Max('total_marks'),
        min_marks=Min('total_marks'),
        total_students=Count('id'),
        distinctions=Count('id', filter=F('total_marks') >= 80),
        credits=Count('id', filter=F('total_marks').range(65, 79.99)),
        passes=Count('id', filter=F('total_marks').range(40, 64.99)),
        fails=Count('id', filter=F('total_marks') < 40)
    ).order_by('-avg_marks')
    
    context = {
        'exam': exam,
        'subject_stats': subject_stats
    }
    return render(request, 'exams/subject_analysis.html', context)

@login_required
@permission_required('exams.add_examresult')
def upload_results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        if 'results_file' not in request.FILES:
            messages.error(request, 'Please select a file to upload.')
            return redirect('exams:exam_detail', exam_id=exam_id)
            
        csv_file = TextIOWrapper(request.FILES['results_file'].file, encoding='utf-8')
        try:
            with transaction.atomic():
                processed = process_results_upload(exam, csv_file)
                messages.success(request, f'Successfully processed {processed} results.')
            return redirect('exams:exam_detail', exam_id=exam_id)
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('exams:exam_detail', exam_id=exam_id)
            
    return render(request, 'exams/upload_results.html', {'exam': exam})

@login_required
def exam_results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    results = ExamResult.objects.filter(exam=exam).select_related('student', 'subject')
    
    # Filter by student, subject, or stream if provided
    student_id = request.GET.get('student')
    subject_id = request.GET.get('subject')
    stream = request.GET.get('stream')
    
    if student_id:
        results = results.filter(student_id=student_id)
    if subject_id:
        results = results.filter(subject_id=subject_id)
    if stream:
        results = results.filter(student__stream=stream)
        
    # Get unique subjects and streams for filtering
    subjects = Subject.objects.filter(examresult__exam=exam).distinct()
    streams = Student.objects.filter(examresult__exam=exam).values_list('stream', flat=True).distinct()
    student_id = request.GET.get('student')
    subject_id = request.GET.get('subject')
    
    if student_id:
        results = results.filter(student__id=student_id)
    if subject_id:
        results = results.filter(subject__id=subject_id)
    
    students = Student.objects.filter(form_level=exam.form_level, is_active=True)
    subjects = Subject.objects.filter(is_active=True)
    
    context = {
        'exam': exam,
        'results': results,
        'students': students,
        'subjects': subjects,
        'selected_student': student_id,
        'selected_subject': subject_id,
    }
    return render(request, 'exams/exam_results.html', context)

@login_required
def enter_results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        # Process form submission for entering results
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        marks = request.POST.get('marks')
        
        if student_id and subject_id and marks:
            from .services import ExamResultsService
            
            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)
            
            # Create or update exam result
            result, created = ExamResult.objects.get_or_create(
                exam=exam,
                student=student,
                subject=subject,
                defaults={'marks': int(marks), 'entered_by': request.user}
            )
            
            if not created:
                result.marks = int(marks)
                result.entered_by = request.user
                result.save()
            
            # Automatically recalculate rankings for this exam
            ExamResultsService.recalculate_exam_rankings(exam.id)
            
            messages.success(request, f'Result entered for {student.name} in {subject.name}. Rankings updated.')
            return redirect('exams:enter_results', exam_id=exam.id)
    
    # Get students for this form level
    students = Student.objects.filter(form_level=exam.form_level, is_active=True)
    subjects = Subject.objects.filter(is_active=True)
    
    context = {
        'exam': exam,
        'students': students,
        'subjects': subjects,
    }
    return render(request, 'exams/enter_results.html', context)