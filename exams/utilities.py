# exams/utilities.py
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Avg
from decimal import Decimal
from students.models import Student
from .models import Exam, ExamResult, GradingSystem, SubjectCategory, GradingRange, PaperResult

class ExamResultsService:
    @staticmethod
    def get_student_exam_summary(exam_id):
        """
        Calculates a summary of each student's performance for a given exam.
        Returns a dictionary of student summaries.
        """
        exam = Exam.objects.get(pk=exam_id)
        students = Student.objects.filter(form_level=exam.form_level, school=exam.school, is_active=True).order_by('stream', 'name')

        student_data = {}
        all_subjects = {}

        for student in students:
            # Prefetch PaperResults to minimize queries
            paper_results = PaperResult.objects.filter(
                exam=exam,
                student=student
            ).select_related('subject_paper', 'subject_paper__subject')

            subject_marks = {}
            total_exam_marks = Decimal(0)
            total_points = Decimal(0)
            subject_count = 0

            # Step 1: Aggregate paper marks into subjects and calculate total marks/points
            for paper_result in paper_results:
                subject_name = paper_result.subject_paper.subject.name
                all_subjects[subject_name] = True
                
                # Check if we have a valid max_marks and contribution for the subject
                # This prevents division by zero if data is missing
                if paper_result.subject_paper.max_marks > 0 and paper_result.subject_paper.contribution_percentage > 0:
                    normalized_marks = (paper_result.marks / paper_result.subject_paper.max_marks) * 100
                else:
                    normalized_marks = 0

                if subject_name not in subject_marks:
                    subject_marks[subject_name] = {
                        'total_marks': Decimal(0),
                        'total_contribution': Decimal(0),
                        'grade': None,
                        'points': None
                    }

                subject_marks[subject_name]['total_marks'] += normalized_marks * (Decimal(paper_result.subject_paper.contribution_percentage) / 100)
                subject_marks[subject_name]['total_contribution'] += Decimal(paper_result.subject_paper.contribution_percentage)

            # Step 2: Calculate subject grades and points
            for subject_name, data in subject_marks.items():
                if data['total_contribution'] > 0:
                    final_subject_marks = data['total_marks'] / (data['total_contribution'] / 100)
                    
                    # Find the grading system for the subject and get the grade/points
                    try:
                        subject = all_subjects.get(subject_name)
                        category = subject.category
                        grading_system = GradingSystem.objects.get(
                            is_active=True,
                            subject_category=category
                        )
                        grading_range = GradingRange.objects.get(
                            grading_system=grading_system,
                            min_marks__lte=final_subject_marks,
                            max_marks__gte=final_subject_marks
                        )
                        data['grade'] = grading_range.grade
                        data['points'] = grading_range.points
                        total_points += grading_range.points
                        total_exam_marks += final_subject_marks
                        subject_count += 1
                    except (GradingSystem.DoesNotExist, GradingRange.DoesNotExist):
                        # Fallback if no grading system found
                        data['grade'] = 'N/A'
                        data['points'] = 0

            mean_marks = total_exam_marks / subject_count if subject_count > 0 else Decimal(0)
            mean_grade = ExamResultsService.calculate_mean_grade_from_points(total_points, subject_count)

            student_data[student.admission_number] = {
                'admission_no': student.admission_number,
                'name': student.name,
                'stream': student.stream,
                'total_marks': total_exam_marks,
                'mean_marks': mean_marks,
                'total_points': total_points,
                'mean_grade': mean_grade,
                'num_subjects': subject_count,
                'subject_marks': { k: v['grade'] for k, v in subject_marks.items() },
            }
        
        return student_data
    
    @staticmethod
    def calculate_mean_grade_from_points(total_points, num_subjects):
        """Calculates the mean grade based on total points and number of subjects."""
        if num_subjects == 0:
            return 'E'
        mean_points = total_points / num_subjects
        # This is a simplified grading, we can make this more robust
        if mean_points >= 10.5:
            return 'A'
        elif mean_points >= 9.5:
            return 'B'
        elif mean_points >= 8.5:
            return 'C'
        elif mean_points >= 7.5:
            return 'D'
        else:
            return 'E'

    @staticmethod
    def calculate_positions(student_data):
        """
        Calculates stream and overall positions based on total points.
        Returns the updated student_data dictionary.
        """
        # Overall position
        sorted_overall = sorted(student_data.values(), key=lambda x: x['total_points'], reverse=True)
        for i, student in enumerate(sorted_overall, 1):
            student['class_position'] = f"{i}/{len(sorted_overall)}"

        # Stream position
        streams = {}
        for student in sorted_overall:
            if student['stream'] not in streams:
                streams[student['stream']] = []
            streams[student['stream']].append(student)

        for stream, students in streams.items():
            for i, student in enumerate(students, 1):
                student['stream_position'] = f"{i}/{len(students)}"

        return student_data
