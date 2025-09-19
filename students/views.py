from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from .models import Student, Subject
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
    
    # Get student summaries for this exam, ordered by total marks (descending)
    summaries = StudentExamSummary.objects.filter(exam=exam).order_by('-total_marks')
    
    # Filter by stream if provided
    stream = request.GET.get('stream')
    if stream:
        summaries = summaries.filter(student__stream=stream)
    
    context = {
        'exam': exam,
        'summaries': summaries,
        'selected_stream': stream,
        'streams': ['East', 'West', 'North', 'South'],
    }
    return render(request, 'students/merit_list.html', context)