from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from ..models import Exam, Subject, SubjectPaper
from ..utils.spreadsheet import SpreadsheetTemplate
import io

class SpreadsheetTemplateView(LoginRequiredMixin, View):
    def get(self, request, exam_id, subject_id, paper_id=None):
        """Download spreadsheet template"""
        exam = get_object_or_404(Exam, pk=exam_id)
        subject = get_object_or_404(Subject, pk=subject_id)
        paper = get_object_or_404(SubjectPaper, pk=paper_id) if paper_id else None
        
        # Generate template
        template = SpreadsheetTemplate(exam, subject, paper)
        workbook = template.generate_template()
        
        # Create response
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        # Generate filename
        filename = f"{exam.name}_{subject.name}"
        if paper:
            filename += f"_{paper.name}"
        filename += "_template.xlsx"
        
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def post(self, request, exam_id, subject_id, paper_id=None):
        """Upload filled spreadsheet"""
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
            
        file = request.FILES['file']
        
        # Validate spreadsheet
        is_valid, message = SpreadsheetTemplate.validate_spreadsheet(file)
        if not is_valid:
            return JsonResponse({'error': message}, status=400)
        
        try:
            # Process spreadsheet
            results = SpreadsheetTemplate.process_spreadsheet(
                file, exam_id, subject_id, paper_id
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully processed {len(results)} results',
                'count': len(results)
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Error processing spreadsheet: {str(e)}'
            }, status=500)