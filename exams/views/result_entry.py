from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.forms import formset_factory
from ..models import PaperResult, Exam
from ..forms.bulk_entry import BulkPaperResultEntryForm
from ..forms.result_entry import PaperResultRow, BulkResultUploadForm
from students.models import Student, StudentSubjectEnrollment
from decimal import Decimal
import pandas as pd

class BulkPaperResultEntryView(LoginRequiredMixin, TemplateView):
    template_name = 'exams/bulk_paper_result_entry.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entry_form'] = BulkPaperResultEntryForm(user=self.request.user)
        context['upload_form'] = BulkResultUploadForm()
        return context
    
    def post(self, request, *args, **kwargs):
        entry_form = BulkPaperResultEntryForm(request.POST, user=request.user)
        
        if entry_form.is_valid():
            exam = entry_form.cleaned_data['exam']
            subject = entry_form.cleaned_data['subject']
            entry_mode = entry_form.cleaned_data['entry_mode']
            
            # Get students without results
            students = Student.objects.filter(
                form_level__in=exam.participating_forms.all()
            ).filter(
                studentsubjectenrollment__subject=subject,
                studentsubjectenrollment__is_enrolled=True
            ).exclude(
                paperresult__exam=exam,
                paperresult__subject=subject
            ).order_by('admission_number')
            
            # Create formset for student results
            PaperResultFormSet = formset_factory(PaperResultRow, extra=0)
            initial_data = [{'student': student} for student in students]
            
            if entry_mode == 'normal':
                max_marks = entry_form.cleaned_data['max_marks']
            else:
                paper = entry_form.cleaned_data['paper']
                max_marks = paper.max_marks
            
            formset = PaperResultFormSet(initial=initial_data)
            
            context = self.get_context_data()
            context.update({
                'entry_form': entry_form,
                'formset': formset,
                'max_marks': max_marks,
                'exam': exam,
                'subject': subject,
                'entry_mode': entry_mode,
            })
            
            return render(request, self.template_name, context)
            
        context = self.get_context_data()
        context['entry_form'] = entry_form
        return render(request, self.template_name, context)
    
    @transaction.atomic
    def save_results(self, request):
        formset = PaperResultFormSet(request.POST)
        entry_form = BulkPaperResultEntryForm(request.POST, user=request.user)
        
        if not (formset.is_valid() and entry_form.is_valid()):
            raise ValidationError("Invalid form data")
            
        exam = entry_form.cleaned_data['exam']
        subject = entry_form.cleaned_data['subject']
        entry_mode = entry_form.cleaned_data['entry_mode']
        
        if entry_mode == 'normal':
            max_marks = entry_form.cleaned_data['max_marks']
            paper = None
        else:
            paper = entry_form.cleaned_data['paper']
            max_marks = paper.max_marks
        
        results = []
        for form in formset:
            if form.is_valid():
                data = form.cleaned_data
                student = data['student']
                marks = data['marks']
                status = data['status']
                
                # Convert marks to percentage if needed
                if marks and max_marks != 100:
                    marks = (Decimal(marks) / Decimal(max_marks)) * 100
                
                result = PaperResult(
                    exam=exam,
                    student=student,
                    subject=subject,
                    paper=paper,
                    marks=marks,
                    status=status,
                    entered_by=request.user
                )
                results.append(result)
        
        PaperResult.objects.bulk_create(results)
        messages.success(request, f"{len(results)} results saved successfully")
        
    def handle_file_upload(self, request):
        form = BulkResultUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['result_file']
            has_headers = form.cleaned_data['has_headers']
            
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                    
                if not has_headers:
                    df.columns = ['admission_number', 'marks', 'status']
                
                # Process the data
                results = self.process_uploaded_results(df, request)
                messages.success(request, f"{len(results)} results imported successfully")
                
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
                
        return redirect('bulk_paper_result_entry')