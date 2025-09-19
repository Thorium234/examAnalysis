from django.db.models import Sum, Count, Avg
from .models import ExamResult, StudentExamSummary, Exam
from students.models import Student

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