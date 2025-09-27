from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import random
from exams.models import (
    Exam, PaperResult, ExamResult, GradingSystem, GradingRange,
    StudentExamSummary
)
from students.models import Student
from subjects.models import Subject, SubjectPaper
from school.models import School


class Command(BaseCommand):
    help = 'Generate comprehensive exam results for all students across all subjects for existing exams'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school',
            type=str,
            help='School name to generate results for (optional, defaults to first school)',
        )
        parser.add_argument(
            '--exam-id',
            type=int,
            help='Specific exam ID to generate results for (optional, generates for all exams)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting exam results generation...'))

        # Get school
        if options['school']:
            try:
                school = School.objects.get(name=options['school'])
            except School.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'School "{options["school"]}" not found'))
                return
        else:
            school = School.objects.first()
            if not school:
                self.stdout.write(self.style.ERROR('No schools found in database'))
                return

        self.stdout.write(f'Generating results for school: {school.name}')

        # Get exams
        if options['exam_id']:
            try:
                exams = [Exam.objects.get(id=options['exam_id'], school=school)]
            except Exam.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Exam with ID {options["exam_id"]} not found'))
                return
        else:
            exams = Exam.objects.filter(school=school)

        if not exams:
            self.stdout.write(self.style.WARNING('No exams found'))
            return

        # Ensure grading systems exist
        self.ensure_grading_systems(school)

        total_results_created = 0

        for exam in exams:
            self.stdout.write(f'Processing exam: {exam.name} (Form {exam.form_level})')
            results_count = self.generate_results_for_exam(exam)
            total_results_created += results_count
            self.stdout.write(f'Created {results_count} results for {exam.name}')

        self.stdout.write(self.style.SUCCESS(f'Total results created: {total_results_created}'))
        self.stdout.write(self.style.SUCCESS('Exam results generation completed!'))

    def ensure_grading_systems(self, school):
        """Ensure grading systems exist for all subject categories"""
        from subjects.models import SubjectCategory

        categories = SubjectCategory.objects.filter(school=school)

        for category in categories:
            # Check if grading system exists
            grading_system = GradingSystem.objects.filter(
                school=school,
                subject_category=category,
                is_active=True
            ).first()

            if not grading_system:
                # Create default grading system
                grading_system = GradingSystem.objects.create(
                    name=f'Standard {category.name} Grading',
                    school=school,
                    subject_category=category,
                    is_active=True,
                    is_default=True
                )

                # Create grading ranges (Kenyan system)
                ranges_data = [
                    (80, 100, 'A', 12),
                    (75, 79, 'A-', 11),
                    (70, 74, 'B+', 10),
                    (65, 69, 'B', 9),
                    (60, 64, 'B-', 8),
                    (55, 59, 'C+', 7),
                    (50, 54, 'C', 6),
                    (45, 49, 'C-', 5),
                    (40, 44, 'D+', 4),
                    (35, 39, 'D', 3),
                    (30, 34, 'D-', 2),
                    (0, 29, 'E', 1),
                ]

                for min_marks, max_marks, grade, points in ranges_data:
                    GradingRange.objects.create(
                        grading_system=grading_system,
                        min_marks=min_marks,
                        max_marks=max_marks,
                        grade=grade,
                        points=points
                    )

                self.stdout.write(f'Created grading system for {category.name}')

    @transaction.atomic
    def generate_results_for_exam(self, exam):
        """Generate results for a specific exam"""
        # Get all students in this exam's form level
        students = Student.objects.filter(
            school=exam.school,
            form_level__number=exam.form_level
        )

        if not students:
            self.stdout.write(f'No students found for Form {exam.form_level}')
            return 0

        results_created = 0

        for student in students:
            # Get subjects the student is enrolled in
            enrolled_subjects = student.subjects.all()

            if not enrolled_subjects:
                self.stdout.write(f'Warning: Student {student.name} has no enrolled subjects')
                continue

            for subject in enrolled_subjects:
                # Skip if result already exists
                if ExamResult.objects.filter(exam=exam, student=student, subject=subject).exists():
                    continue

                # Generate paper results
                paper_results = self.generate_paper_results(exam, student, subject)

                if paper_results:
                    # Calculate final marks
                    final_marks = self.calculate_final_marks(subject, paper_results)

                    # Get grade and points
                    grade, points = self.get_grade_and_points(exam.school, subject, final_marks)

                    # Create ExamResult
                    exam_result = ExamResult.objects.create(
                        exam=exam,
                        student=student,
                        subject=subject,
                        final_marks=final_marks,
                        grade=grade,
                        points=points
                    )

                    results_created += 1

        # Update exam summaries after all results are created
        self.update_exam_summaries(exam)

        return results_created

    def generate_paper_results(self, exam, student, subject):
        """Generate realistic marks for each paper of a subject"""
        papers = SubjectPaper.objects.filter(subject=subject)
        paper_results = []

        if not papers:
            return []

        for paper in papers:
            # Generate realistic marks based on paper type and max marks
            marks = self.generate_realistic_marks(paper)

            # Create PaperResult
            paper_result = PaperResult.objects.create(
                exam=exam,
                student=student,
                subject_paper=paper,
                marks=marks
            )

            paper_results.append(paper_result)

        return paper_results

    def generate_realistic_marks(self, paper):
        """Generate realistic marks for a paper based on its type and max marks"""
        max_marks = paper.max_marks

        # Different distributions based on paper type
        if 'Paper 1' in paper.paper_number and max_marks >= 80:
            # Theory papers - normal distribution around 60-70%
            mean = max_marks * 0.65
            std_dev = max_marks * 0.15
        elif 'Paper 2' in paper.paper_number:
            if max_marks >= 80:
                # Second theory paper - slightly lower
                mean = max_marks * 0.60
                std_dev = max_marks * 0.18
            else:
                # Literature or other Paper 2
                mean = max_marks * 0.55
                std_dev = max_marks * 0.20
        elif 'Paper 3' in paper.paper_number:
            # Practical/oral papers - can be higher or lower
            mean = max_marks * 0.70
            std_dev = max_marks * 0.12
        else:
            # Default distribution
            mean = max_marks * 0.60
            std_dev = max_marks * 0.20

        # Generate marks using normal distribution, clamped to 0-max_marks
        marks = random.gauss(mean, std_dev)
        marks = max(0, min(max_marks, round(marks)))

        return marks

    def calculate_final_marks(self, subject, paper_results):
        """Calculate final marks based on paper contributions"""
        total_weighted_marks = 0
        total_contribution = 0

        for paper_result in paper_results:
            paper = paper_result.subject_paper
            # Normalize to 100 marks scale
            normalized_marks = (paper_result.marks / paper.max_marks) * 100
            # Apply contribution percentage
            weighted_marks = normalized_marks * (paper.contribution_percentage / 100)
            total_weighted_marks += weighted_marks
            total_contribution += paper.contribution_percentage

        # If total contribution < 100%, scale up
        if total_contribution < 100:
            final_marks = (total_weighted_marks * 100) / total_contribution
        else:
            final_marks = total_weighted_marks

        return round(final_marks, 2)

    def get_grade_and_points(self, school, subject, marks):
        """Get grade and points based on grading system"""
        try:
            # Find grading system for subject's category
            if subject.category:
                grading_system = GradingSystem.objects.filter(
                    school=school,
                    subject_category=subject.category,
                    is_active=True
                ).first()
            else:
                grading_system = None

            # Find appropriate grade range
            grade_range = GradingRange.objects.filter(
                grading_system=grading_system,
                min_marks__lte=marks,
                max_marks__gte=marks
            ).first()

            if grade_range:
                return grade_range.grade, grade_range.points

        except (GradingSystem.DoesNotExist, GradingRange.DoesNotExist):
            pass

        # Fallback grading
        if marks >= 80:
            return 'A', 12
        elif marks >= 75:
            return 'A-', 11
        elif marks >= 70:
            return 'B+', 10
        elif marks >= 65:
            return 'B', 9
        elif marks >= 60:
            return 'B-', 8
        elif marks >= 55:
            return 'C+', 7
        elif marks >= 50:
            return 'C', 6
        elif marks >= 45:
            return 'C-', 5
        elif marks >= 40:
            return 'D+', 4
        elif marks >= 35:
            return 'D', 3
        elif marks >= 30:
            return 'D-', 2
        else:
            return 'E', 1

    def update_exam_summaries(self, exam):
        """Update student exam summaries and rankings"""
        students = Student.objects.filter(
            exam_results__exam=exam
        ).distinct()

        for student in students:
            results = ExamResult.objects.filter(exam=exam, student=student)

            if not results:
                continue

            total_marks = sum(result.final_marks for result in results)
            total_points = sum(result.points for result in results if result.points)
            subject_count = results.count()

            mean_marks = total_marks / subject_count if subject_count > 0 else 0
            mean_points = total_points / subject_count if subject_count > 0 else 0

            # Calculate mean grade from mean points
            mean_grade = self.points_to_grade(mean_points)

            # Calculate positions (simplified)
            stream_position = self.calculate_stream_position(exam, student, mean_marks)
            overall_position = self.calculate_overall_position(exam, student, mean_marks)

            StudentExamSummary.objects.update_or_create(
                exam=exam,
                student=student,
                defaults={
                    'total_marks': total_marks,
                    'mean_marks': mean_marks,
                    'mean_grade': mean_grade,
                    'total_points': total_points,
                    'stream_position': stream_position,
                    'overall_position': overall_position
                }
            )

    def points_to_grade(self, mean_points):
        """Convert mean points to mean grade"""
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

    def calculate_stream_position(self, exam, student, mean_marks):
        """Calculate position within student's stream"""
        stream_students = Student.objects.filter(
            school=exam.school,
            form_level__number=exam.form_level,
            stream=student.stream
        )

        # Get mean marks for all students in stream
        stream_means = []
        for s in stream_students:
            results = ExamResult.objects.filter(exam=exam, student=s)
            if results:
                s_mean = sum(r.final_marks for r in results) / results.count()
                stream_means.append(s_mean)

        stream_means.sort(reverse=True)
        position = stream_means.index(mean_marks) + 1 if mean_marks in stream_means else len(stream_means) + 1

        return position

    def calculate_overall_position(self, exam, student, mean_marks):
        """Calculate overall position in the form"""
        form_students = Student.objects.filter(
            school=exam.school,
            form_level__number=exam.form_level
        )

        # Get mean marks for all students in form
        form_means = []
        for s in form_students:
            results = ExamResult.objects.filter(exam=exam, student=s)
            if results:
                s_mean = sum(r.final_marks for r in results) / results.count()
                form_means.append(s_mean)

        form_means.sort(reverse=True)
        position = form_means.index(mean_marks) + 1 if mean_marks in form_means else len(form_means) + 1

        return position