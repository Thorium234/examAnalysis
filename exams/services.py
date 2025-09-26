# exams/services.py
from django.db.models import Sum, Count, Avg, Min, Max
from decimal import Decimal
from django.db import transaction
from .models import ExamResult, StudentExamSummary, Exam, PaperResult
from students.models import Student, Subject
import csv


def calculate_exam_statistics(exam):
    """Calculate comprehensive exam statistics"""
    results = ExamResult.objects.filter(exam=exam)
    summaries = StudentExamSummary.objects.filter(exam=exam)

    stats = {
        'total_students': results.values('student').distinct().count(),
        'total_subjects': results.values('subject').distinct().count(),
        'average_marks': results.aggregate(avg_marks=Avg('total_marks'))['avg_marks'],
        'mean_points': summaries.aggregate(avg_points=Avg('mean_points'))['avg_points'],
        'grade_distribution': {
            'A': results.filter(total_marks__gte=80).count(),
            'B': results.filter(total_marks__range=(65, 79.99)).count(),
            'C': results.filter(total_marks__range=(50, 64.99)).count(),
            'D': results.filter(total_marks__range=(40, 49.99)).count(),
            'E': results.filter(total_marks__lt=40).count()
        }
    }
    return stats

def process_results_upload(exam, csv_file):
    """Process a CSV file containing exam results"""
    reader = csv.DictReader(csv_file)
    processed = 0
    
    for row in reader:
        try:
            student = Student.objects.get(admission_number=row['Admission Number'])
            subject = Subject.objects.get(name=row['Subject'])
            marks = float(row['Marks'])
            
            if 0 <= marks <= 100:
                result, created = ExamResult.objects.update_or_create(
                    exam=exam,
                    student=student,
                    subject=subject,
                    defaults={'total_marks': marks}
                )
                result.calculate_grade()
                result.save()
                processed += 1
                
        except (Student.DoesNotExist, Subject.DoesNotExist, ValueError) as e:
            continue
            
    # After processing all results, update summaries
    update_exam_summaries(exam)
    return processed

def update_exam_summaries(exam):
    """Update all student summaries for an exam"""
    students = Student.objects.filter(examresult__exam=exam).distinct()
    
    for student in students:
        results = ExamResult.objects.filter(exam=exam, student=student)
        total_marks = results.aggregate(total=Sum('total_marks'))['total']
        mean_marks = results.aggregate(avg=Avg('total_marks'))['avg']
        
        # Calculate positions
        stream_position = calculate_stream_position(exam, student, mean_marks)
        overall_position = calculate_overall_position(exam, student, mean_marks)
        
        StudentExamSummary.objects.update_or_create(
            exam=exam,
            student=student,
            defaults={
                'total_marks': total_marks,
                'mean_marks': mean_marks,
                'stream_position': stream_position,
                'overall_position': overall_position
            }
        )

class ExamResultsService:
    """Service class to handle exam result calculations and ranking"""
    
    @staticmethod
    def calculate_student_summary(exam, student):
        """Calculate summary for a specific student in an exam"""
        results = ExamResult.objects.filter(exam=exam, student=student)
        
        if not results.exists():
            return None
        
        total_marks = sum(result.marks for result in results)
        total_points = sum(result.points for result in results)
        subjects_count = results.count()
        mean_marks = total_marks / subjects_count if subjects_count > 0 else 0
        
        # Calculate mean grade based on points average
        mean_points = total_points / subjects_count if subjects_count > 0 else 0
        mean_grade = ExamResultsService.get_mean_grade_from_points(mean_points)
        
        # Create or update the summary
        summary, created = StudentExamSummary.objects.update_or_create(
            exam=exam,
            student=student,
            defaults={
                'total_marks': total_marks,
                'total_points': total_points,
                'mean_marks': mean_marks,
                'mean_grade': mean_grade,
                'subjects_count': subjects_count,
            }
        )
        
        return summary
    
    @staticmethod
    def get_mean_grade_from_points(mean_points):
        """Convert mean points to mean grade using Kenyan grading system"""
        if mean_points >= 11.5:
            return 'A'
        elif mean_points >= 10.5:
            return 'A-'
        elif mean_points >= 9.5:
            return 'B+'
        elif mean_points >= 8.5:
            return 'B'
        elif mean_points >= 7.5:
            return 'B-'
        elif mean_points >= 6.5:
            return 'C+'
        elif mean_points >= 5.5:
            return 'C'
        elif mean_points >= 4.5:
            return 'C-'
        elif mean_points >= 3.5:
            return 'D+'
        elif mean_points >= 2.5:
            return 'D'
        elif mean_points >= 1.5:
            return 'D-'
        else:
            return 'E'
    
    @staticmethod
    def calculate_all_summaries_for_exam(exam):
        """Calculate summaries for all students in an exam"""
        students_with_results = Student.objects.filter(
            exam_results__exam=exam,
            form_level=exam.form_level
        ).distinct()
        
        for student in students_with_results:
            ExamResultsService.calculate_student_summary(exam, student)
        
        # Now calculate positions
        ExamResultsService.calculate_positions(exam)
    
    @staticmethod
    def calculate_positions(exam):
        """Calculate overall and stream positions using Chinese technique (merit order)"""
        # Get all summaries for this exam ordered by total marks (descending)
        # Chinese technique: Higher total marks = better position, ties broken by total points
        summaries = StudentExamSummary.objects.filter(exam=exam).order_by(
            '-total_marks', '-total_points', 'student__name'
        )
        
        # Calculate overall positions
        for position, summary in enumerate(summaries, 1):
            summary.overall_position = position
            summary.total_students_overall = summaries.count()
            summary.save(update_fields=['overall_position', 'total_students_overall'])
        
        # Calculate stream positions
        streams = summaries.values_list('student__stream', flat=True).distinct()
        
    @staticmethod
    def calculate_final_marks(exam_id, student_id, subject_id):
        """Calculate final marks for a subject based on paper results and their contribution percentages"""
        # Get all paper results for this exam-student-subject combination
        paper_results = PaperResult.objects.filter(
            exam_id=exam_id,
            student_id=student_id,
            subject_id=subject_id
        ).select_related('paper')
        
        # Get the contribution percentages for each paper
        paper_ratios = SubjectPaperRatio.objects.filter(
            subject_id=subject_id,
            is_active=True
        ).select_related('paper')
        
        # If no results or no ratios, return None
        if not paper_results.exists() or not paper_ratios.exists():
            return None, 'P'
        
        total_marks = Decimal('0.0')
        total_contribution = Decimal('0.0')
        
        # Check if student was absent or disqualified in any paper
        if any(r.status == 'A' for r in paper_results):
            return Decimal('-1.0'), 'A'  # Absent
        if any(r.status == 'D' for r in paper_results):
            return Decimal('-2.0'), 'D'  # Disqualified
        
        # Calculate weighted average
        for ratio in paper_ratios:
            result = next(
                (r for r in paper_results if r.paper_id == ratio.paper_id),
                None
            )
            if result:
                # Convert marks to percentage of paper's max marks
                paper_percentage = (result.marks / ratio.paper.max_marks) * 100
                # Apply contribution percentage
                contribution = (paper_percentage * ratio.contribution_percentage / 100)
                total_marks += contribution
                total_contribution += ratio.contribution_percentage
        
        # If we don't have 100% contribution, scale up the marks
        if total_contribution < 100:
            total_marks = (total_marks * 100) / total_contribution
        
        return round(total_marks, 2), 'P'
    
    @staticmethod
    @transaction.atomic
    def update_exam_result(exam_id, student_id, subject_id):
        """Update or create an ExamResult based on PaperResults"""
        total_marks, status = ExamResultsService.calculate_final_marks(
            exam_id, student_id, subject_id
        )
        
        if total_marks is None:
            return None
            
        result, created = ExamResult.objects.update_or_create(
            exam_id=exam_id,
            student_id=student_id,
            subject_id=subject_id,
            defaults={
                'total_marks': total_marks,
                'status': status
            }
        )
        
        return result
        
        for stream in streams:
            stream_summaries = summaries.filter(student__stream=stream)
            stream_count = stream_summaries.count()
            
            for position, summary in enumerate(stream_summaries, 1):
                summary.stream_position = position
                summary.total_students_in_stream = stream_count
                summary.save(update_fields=['stream_position', 'total_students_in_stream'])
    
    @staticmethod
    def calculate_subject_rankings(exam):
        """Calculate rankings within each subject for an exam"""
        from students.models import Subject
        
        subjects = Subject.objects.filter(
            examresult__exam=exam
        ).distinct()
        
        for subject in subjects:
            results = ExamResult.objects.filter(
                exam=exam, 
                subject=subject
            ).order_by('-marks', 'student__name')
            
            total_students = results.count()
            
            for rank, result in enumerate(results, 1):
                result.rank_in_subject = rank
                result.total_students_in_subject = total_students
                result.save(update_fields=['rank_in_subject', 'total_students_in_subject'])
    
    @staticmethod
    def recalculate_exam_rankings(exam_id):
        """Main method to recalculate all rankings for an exam"""
        try:
            exam = Exam.objects.get(id=exam_id)
            
            # Step 1: Calculate individual student summaries
            ExamResultsService.calculate_all_summaries_for_exam(exam)
            
            # Step 2: Calculate subject rankings
            ExamResultsService.calculate_subject_rankings(exam)
            
            return True
        except Exam.DoesNotExist:
            return False
