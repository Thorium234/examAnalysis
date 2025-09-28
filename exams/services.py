from django.db.models import Avg, Count, Sum, F, Q
from .models import ExamResult, StudentExamSummary, GradingSystem, GradingRange, PaperResult
from students.models import Student
from subjects.models import Subject
import logging

logger = logging.getLogger(__name__)

class GradingService:
    """
    Service class for handling grading calculations including best of 7 subjects logic
    """

    @staticmethod
    def calculate_subject_final_marks(exam, student, subject):
        """
        Calculate final marks for a subject considering paper ratios.
        """
        from subjects.models import SubjectPaperRatio

        # Get all paper results for this exam, student, and subject
        paper_results = PaperResult.objects.filter(
            exam=exam,
            student=student,
            subject_paper__subject=subject
        ).select_related('subject_paper')

        if not paper_results.exists():
            return 0

        total_weighted_marks = 0
        total_weight = 0

        for paper_result in paper_results:
            # Get the contribution ratio for this paper
            ratio = SubjectPaperRatio.objects.filter(
                subject=subject,
                paper=paper_result.subject_paper
            ).first()

            if ratio:
                weight = ratio.contribution_percentage / 100.0
                total_weighted_marks += paper_result.marks * weight
                total_weight += weight

        # If no ratios defined, use simple average
        if total_weight == 0:
            return sum(p.marks for p in paper_results) / len(paper_results)

        return total_weighted_marks / total_weight if total_weight > 0 else 0

    @staticmethod
    def calculate_best_of_seven(exam_results):
        """
        Calculate the best 7 subjects from a list of exam results.
        Returns a tuple of (best_results, excluded_results, total_marks, total_points)
        """
        if len(exam_results) <= 7:
            # If 7 or fewer subjects, use all of them
            best_results = exam_results
            excluded_results = []
        else:
            # Sort by marks descending and take top 7
            sorted_results = sorted(exam_results, key=lambda x: x.final_marks, reverse=True)
            best_results = sorted_results[:7]
            excluded_results = sorted_results[7:]

        # Calculate totals
        total_marks = sum(result.final_marks for result in best_results)
        total_points = sum(result.points or 0 for result in best_results)

        return best_results, excluded_results, total_marks, total_points

    @staticmethod
    def calculate_student_exam_summary(student, exam):
        """
        Calculate and update the exam summary for a student.
        Implements the best of 7 subjects logic with paper ratios.
        """
        try:
            # Get all subjects the student took in this exam
            subjects = Subject.objects.filter(
                examresult__student=student,
                examresult__exam=exam
            ).distinct()

            exam_results = []
            for subject in subjects:
                # Calculate final marks for each subject using paper ratios
                final_marks = GradingService.calculate_subject_final_marks(exam, student, subject)

                # Get or create exam result
                exam_result, created = ExamResult.objects.get_or_create(
                    exam=exam,
                    student=student,
                    subject=subject,
                    defaults={'final_marks': final_marks}
                )

                # Update final marks if not created
                if not created:
                    exam_result.final_marks = final_marks
                    exam_result.save()

                # Calculate grade and points
                grading_system = GradingSystem.objects.filter(
                    school=exam.school,
                    is_active=True
                ).first()

                if grading_system:
                    grade, points = grading_system.get_grade_and_points(final_marks)
                    exam_result.grade = grade
                    exam_result.points = points
                    exam_result.save()

                exam_results.append(exam_result)

            if not exam_results:
                logger.warning(f"No exam results found for student {student} in exam {exam}")
                return None

            # Calculate best of 7
            best_results, excluded_results, best_marks, best_points = GradingService.calculate_best_of_seven(exam_results)

            # Calculate mean marks and grade from best 7
            subjects_count = len(exam_results)
            mean_marks = best_marks / 7 if best_results else 0

            if grading_system:
                # Calculate mean grade and points
                mean_grade, mean_points = grading_system.get_grade_and_points(mean_marks)
            else:
                mean_grade = 'N/A'
                mean_points = 0

            # Calculate positions (stream and overall)
            stream_position, overall_position = GradingService.calculate_positions(student, exam, best_marks)

            # Update or create summary
            summary, created = StudentExamSummary.objects.update_or_create(
                student=student,
                exam=exam,
                defaults={
                    'total_marks': sum(r.final_marks for r in exam_results),
                    'mean_marks': mean_marks,
                    'mean_grade': mean_grade,
                    'total_points': sum(r.points or 0 for r in exam_results),
                    'stream_position': stream_position,
                    'overall_position': overall_position,
                    'subjects_count': subjects_count,
                    'best_of_seven_marks': best_marks,
                    'best_of_seven_points': best_points,
                    'excluded_subjects': [r.subject.id for r in excluded_results],
                }
            )

            logger.info(f"Updated exam summary for student {student} in exam {exam}")
            return summary

        except Exception as e:
            logger.error(f"Error calculating exam summary for student {student}: {e}")
            return None

    @staticmethod
    def calculate_positions(student, exam, best_marks):
        """
        Calculate stream and overall positions for a student.
        """
        # Get all students in the same form level and exam
        form_students = Student.objects.filter(
            school=exam.school,
            form_level=student.form_level
        )

        # Get their best marks for comparison
        student_summaries = StudentExamSummary.objects.filter(
            exam=exam,
            student__in=form_students
        ).select_related('student')

        # Calculate positions
        all_marks = [(s.best_of_seven_marks or 0, s.student.stream) for s in student_summaries]
        all_marks.append((best_marks, student.stream))
        all_marks.sort(key=lambda x: x[0], reverse=True)

        # Find positions
        overall_position = 1
        stream_position = 1
        current_marks = best_marks

        for marks, stream in all_marks:
            if marks > current_marks:
                overall_position += 1
                if stream == student.stream:
                    stream_position += 1
            elif marks == current_marks:
                # Handle ties - same position
                pass
            else:
                break

        return stream_position, overall_position

    @staticmethod
    def bulk_calculate_exam_summaries(exam):
        """
        Calculate exam summaries for all students in an exam.
        """
        students = Student.objects.filter(
            school=exam.school,
            form_level__in=exam.participating_forms.all()
        )

        summaries = []
        for student in students:
            summary = GradingService.calculate_student_exam_summary(student, exam)
            if summary:
                summaries.append(summary)

        logger.info(f"Calculated summaries for {len(summaries)} students in exam {exam}")
        return summaries

    @staticmethod
    def get_grading_ranges(grading_system):
        """
        Get grading ranges ordered by marks descending.
        """
        return GradingRange.objects.filter(
            grading_system=grading_system
        ).order_by('-max_marks')