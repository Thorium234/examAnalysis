from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db.models import Count, Avg, Min, Max, F, Prefetch
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, TemplateView
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
from subjects.models import Subject, SubjectPaper
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

# Mixins for permissions
class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.profile.roles.filter(name='Teacher').exists()

class HODRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.profile.roles.filter(name='HOD').exists()


# Exam CRUD Views
#----------------------------------------------------------------------
class ExamCreateView(TeacherRequiredMixin, CreateView):
    model = Exam
    fields = ['name', 'year', 'term', 'participating_forms', 'is_ordinary_exam', 'is_consolidated_exam', 'is_kcse', 'is_year_average', 'is_active']
    template_name = 'exams/exam_form.html'
    success_url = reverse_lazy('exam_list')
    
    def form_valid(self, form):
        form.instance.school = self.request.user.school
        return super().form_valid(form)

class ExamUpdateView(TeacherRequiredMixin, UpdateView):
    model = Exam
    fields = ['name', 'year', 'term', 'participating_forms', 'is_ordinary_exam', 'is_consolidated_exam', 'is_kcse', 'is_year_average', 'is_active']
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
        return Exam.objects.filter(school=self.request.user.school).order_by('-year', '-term')


# Exam Results Entry and Management
#----------------------------------------------------------------------
@login_required
@permission_required('exams.add_examresult', raise_exception=True)
def exam_results_entry(request, pk):
    exam = get_object_or_404(Exam, pk=pk, school=request.user.school)
    students = Student.objects.filter(
        school=request.user.school,
        form_level__in=exam.participating_forms.all()
    ).order_by('stream', 'admission_number')
    
    subjects = Subject.objects.filter(
        form_level__in=exam.participating_forms.all(),
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
                for student in students:
                    for subject in subjects:
                        for paper in subject.papers.all():
                            field_name = f'score_{student.pk}_{subject.pk}_{paper.paper_number}'
                            score_str = request.POST.get(field_name, '')
                            score = int(score_str) if score_str else 0
                            
                            ExamResult.objects.update_or_create(
                                exam=exam,
                                student=student,
                                subject_paper=paper,
                                defaults={'score': score}
                            )
                messages.success(request, "Exam results saved successfully.")
                return redirect('exam_results_entry', pk=pk)
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                
    return render(request, 'exams/exam_results_entry.html', context)

@login_required
@permission_required('exams.add_examresult', raise_exception=True)
def upload_results(request, pk):
    exam = get_object_or_404(Exam, pk=pk, school=request.user.school)
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
        reader = csv.reader(csv_file)
        
        header = next(reader)
        # Expected format: ['Admission Number', 'Subject Name', 'Paper Number', 'Score']
        
        with transaction.atomic():
            for row in reader:
                if len(row) != 4:
                    messages.error(request, f"Skipping invalid row: {row}")
                    continue
                
                try:
                    admission_number, subject_name, paper_number_str, score_str = row
                    
                    student = Student.objects.get(admission_number=admission_number)
                    subject = Subject.objects.get(name__iexact=subject_name)
                    paper = subject.papers.get(paper_number=int(paper_number_str))
                    score = int(score_str)
                    
                    ExamResult.objects.update_or_create(
                        exam=exam,
                        student=student,
                        subject_paper=paper,
                        defaults={'score': score}
                    )
                except Exception as e:
                    messages.error(request, f"Error processing row {row}: {e}")
                    # Rollback transaction on error
                    return redirect('exam_results_entry', pk=pk)
        
        messages.success(request, "CSV file uploaded and results saved successfully.")
        return redirect('exam_results_entry', pk=pk)
    
    messages.error(request, "Please upload a valid CSV file.")
    return redirect('exam_results_entry', pk=pk)

@login_required
def download_exam_results_template(request, pk):
    exam = get_object_or_404(Exam, pk=pk, school=request.user.school)
    students = Student.objects.filter(
        school=request.user.school,
        form_level__in=exam.participating_forms.all()
    ).order_by('admission_number')
    subjects = Subject.objects.filter(
        school=request.user.school,
        form_level__in=exam.participating_forms.all()
    ).prefetch_related('papers')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="exam_template_{exam.name}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Admission Number', 'Subject Name', 'Paper Number', 'Score'])
    
    for student in students:
        for subject in subjects:
            for paper in subject.papers.all():
                writer.writerow([student.admission_number, subject.name, paper.paper_number, ''])
                
    return response

# Exam Analysis and Reports
#----------------------------------------------------------------------
class ExamResultsSummaryView(TeacherRequiredMixin, TemplateView):
    template_name = 'exams/exam_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(Exam, pk=self.kwargs['pk'], school=self.request.user.school)
        
        summary_data = StudentExamSummary.objects.filter(exam=exam).select_related('student')
        
        context['exam'] = exam
        context['summary_data'] = summary_data
        return context

@login_required
def get_exam_summary_data(request, pk):
    try:
        exam = Exam.objects.get(pk=pk, school=request.user.school)
        summary_data = StudentExamSummary.objects.filter(exam=exam).values('student__admission_number', 'student__full_name', 'total_score', 'total_points')
        return JsonResponse(list(summary_data), safe=False)
    except Exam.DoesNotExist:
        return JsonResponse({'error': 'Exam not found'}, status=404)


class StudentReportCardView(TeacherRequiredMixin, TemplateView):
    template_name = 'exams/report_card.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = get_object_or_404(Student, pk=self.kwargs['student_pk'], school=self.request.user.school)
        exam = get_object_or_404(Exam, pk=self.kwargs['exam_pk'], school=self.request.user.school)

        # Get results for the specific student and exam
        results = ExamResult.objects.filter(
            exam=exam,
            student=student
        ).order_by('subject_paper__subject__name', 'subject_paper__paper_number')
        
        context['student'] = student
        context['exam'] = exam
        context['results'] = results
        
        # Calculate totals and grades (requires grading system logic)
        total_score = sum(r.score for r in results)
        total_papers = results.count()
        context['total_score'] = total_score
        
        return context

# Grading System CRUD
#----------------------------------------------------------------------
class GradingSystemListView(HODRequiredMixin, ListView):
    model = GradingSystem
    template_name = 'exams/grading_system_list.html'
    context_object_name = 'grading_systems'

    def get_queryset(self):
        return GradingSystem.objects.filter(school=self.request.user.school)

class GradingSystemCreateView(HODRequiredMixin, CreateView):
    model = GradingSystem
    fields = ['name', 'description', 'is_active']
    template_name = 'exams/grading_system_form.html'
    success_url = reverse_lazy('grading_system_list')

    def form_valid(self, form):
        form.instance.school = self.request.user.school
        return super().form_valid(form)

class GradingSystemUpdateView(HODRequiredMixin, UpdateView):
    model = GradingSystem
    fields = ['name', 'description', 'is_active']
    template_name = 'exams/grading_system_form.html'
    success_url = reverse_lazy('grading_system_list')

class GradingSystemDeleteView(HODRequiredMixin, DeleteView):
    model = GradingSystem
    template_name = 'exams/grading_system_confirm_delete.html'
    success_url = reverse_lazy('grading_system_list')

# Grading Range CRUD
#----------------------------------------------------------------------
class GradingRangeCreateView(HODRequiredMixin, CreateView):
    model = GradingRange
    fields = ['grading_system', 'grade', 'min_score', 'max_score', 'points']
    template_name = 'exams/grading_range_form.html'
    
    def get_success_url(self):
        return reverse_lazy('grading_system_detail', kwargs={'pk': self.object.grading_system.pk})

class GradingRangeUpdateView(HODRequiredMixin, UpdateView):
    model = GradingRange
    fields = ['grade', 'min_score', 'max_score', 'points']
    template_name = 'exams/grading_range_form.html'

    def get_success_url(self):
        return reverse_lazy('grading_system_detail', kwargs={'pk': self.object.grading_system.pk})

class GradingRangeDeleteView(HODRequiredMixin, DeleteView):
    model = GradingRange
    template_name = 'exams/grading_range_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('grading_system_detail', kwargs={'pk': self.object.grading_system.pk})

class GradingSystemDetailView(HODRequiredMixin, TemplateView):
    template_name = 'exams/grading_system_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grading_system = get_object_or_404(GradingSystem, pk=self.kwargs['pk'], school=self.request.user.school)
        grading_ranges = grading_system.grading_ranges.all().order_by('-min_score')
        
        context['grading_system'] = grading_system
        context['grading_ranges'] = grading_ranges
        return context
