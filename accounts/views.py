from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import TeacherSubject, TeacherClass
from students.models import Student
from exams.models import ExamResult

@login_required
def teacher_dashboard(request):
    user = request.user
    
    # Get teacher's subjects and classes
    teacher_subjects = TeacherSubject.objects.filter(teacher=user)
    teacher_classes = TeacherClass.objects.filter(teacher=user)
    
    # Get students in teacher's classes
    class_students = []
    for teacher_class in teacher_classes:
        students = Student.objects.filter(
            form_level=teacher_class.form_level,
            stream=teacher_class.stream,
            is_active=True
        )
        class_students.extend(students)
    
    # Get recent exam results for teacher's subjects
    recent_results = ExamResult.objects.filter(
        subject__name__in=[ts.subject_name for ts in teacher_subjects]
    ).order_by('-date_entered')[:20]
    
    context = {
        'teacher_subjects': teacher_subjects,
        'teacher_classes': teacher_classes,
        'class_students': class_students,
        'recent_results': recent_results,
        'total_students': len(class_students),
    }
    return render(request, 'accounts/teacher_dashboard.html', context)