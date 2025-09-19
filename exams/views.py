from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Exam, ExamResult, StudentExamSummary
from students.models import Student, Subject

@login_required
def exam_list(request):
    exams = Exam.objects.filter(is_active=True).order_by('-date_created')
    
    # Filter by form level if provided
    form_level = request.GET.get('form_level')
    if form_level:
        exams = exams.filter(form_level=form_level)
    
    context = {
        'exams': exams,
        'form_levels': [1, 2, 3, 4],
        'selected_form': form_level,
    }
    return render(request, 'exams/exam_list.html', context)

@login_required
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Get exam statistics
    total_students = ExamResult.objects.filter(exam=exam).values('student').distinct().count()
    total_subjects = ExamResult.objects.filter(exam=exam).values('subject').distinct().count()
    average_marks = ExamResult.objects.filter(exam=exam).aggregate(avg_marks=Avg('marks'))
    
    # Get top performers
    top_performers = StudentExamSummary.objects.filter(exam=exam).order_by('-total_marks')[:10]
    
    context = {
        'exam': exam,
        'total_students': total_students,
        'total_subjects': total_subjects,
        'average_marks': average_marks['avg_marks'],
        'top_performers': top_performers,
    }
    return render(request, 'exams/exam_detail.html', context)

@login_required
def exam_results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    results = ExamResult.objects.filter(exam=exam).select_related('student', 'subject')
    
    # Filter by student or subject if provided
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
            
            messages.success(request, f'Result entered for {student.name} in {subject.name}')
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