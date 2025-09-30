from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from school.models import School, FormLevel, Stream
from students.models import Student
from subjects.models import Subject, SubjectCategory, SubjectPaper, SubjectPaperRatio
from accounts.models import Role, Profile, TeacherSubject, TeacherClass, TeacherGroup, TeacherGroupMembership
from exams.models import GradingSystem, GradingRange, Exam, PaperResult, ExamResult, StudentExamSummary
import csv
import os
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with Kikai Boys High School data from CSV files'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate Kikai data...'))

        # Clear existing data
        self.clear_existing_data()

        # Create school
        school = self.create_school()

        # Create subject categories
        categories = self.create_subject_categories(school)

        # Create subjects
        subjects = self.create_subjects(school, categories)

        # Create form levels and streams
        form_levels, streams = self.create_form_levels_and_streams(school)

        # Create grading system
        grading_system = self.create_grading_system(school)

        # Create roles
        roles = self.create_roles()

        # Create teacher groups
        teacher_groups = self.create_teacher_groups(school)

        # Populate teachers
        teachers = self.populate_teachers(school, roles, teacher_groups, subjects)

        # Populate students and create exam results
        self.create_students_and_exam_results(school, form_levels, subjects, grading_system)

        self.stdout.write(self.style.SUCCESS('Kikai data population completed!'))

    def clear_existing_data(self):
        self.stdout.write('Clearing existing data...')
        StudentExamSummary.objects.all().delete()
        ExamResult.objects.all().delete()
        PaperResult.objects.all().delete()
        Exam.objects.all().delete()
        GradingRange.objects.all().delete()
        GradingSystem.objects.all().delete()
        TeacherClass.objects.all().delete()
        TeacherSubject.objects.all().delete()
        TeacherGroupMembership.objects.all().delete()
        TeacherGroup.objects.all().delete()
        Student.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Role.objects.all().delete()
        Stream.objects.all().delete()
        FormLevel.objects.all().delete()
        SubjectPaperRatio.objects.all().delete()
        SubjectPaper.objects.all().delete()
        Subject.objects.all().delete()
        SubjectCategory.objects.all().delete()
        School.objects.all().delete()
        self.stdout.write('Existing data cleared.')

    def create_school(self):
        school = School.objects.create(
            name='Friends Kikai Boys High School',
            school_code='KIKAI2025',
            location='Chwele, Kenya',
            address='P.O BOX 345 CHWELE',
            phone_number='0710702705',
            email='kikaiboys@gmail.com'
        )
        self.stdout.write(f'Created school: {school.name}')
        return school

    def create_subject_categories(self, school):
        categories_data = [
            ('Languages', 'Language subjects'),
            ('Humanities', 'Humanities subjects'),
            ('Mathematics', 'Mathematics subject'),
            ('Science', 'Science subjects'),
            ('Technicals', 'Technical subjects'),
        ]
        categories = {}
        for name, description in categories_data:
            category = SubjectCategory.objects.create(
                name=name,
                school=school,
                description=description
            )
            categories[name] = category
            self.stdout.write(f'Created subject category: {name}')
        return categories

    def create_subjects(self, school, categories):
        # From exam results, subjects are: ENG, KIS, MAT, BIO, PHY, CHE, HIS, GEO, CRE, AGR, BST
        subjects_data = [
            ('English', 'ENG', 'Languages'),
            ('Kiswahili', 'KIS', 'Languages'),
            ('Mathematics', 'MAT', 'Mathematics'),
            ('Biology', 'BIO', 'Science'),
            ('Physics', 'PHY', 'Science'),
            ('Chemistry', 'CHE', 'Science'),
            ('History and Government', 'HIS', 'Humanities'),
            ('Geography', 'GEO', 'Humanities'),
            ('Christian Religious Education', 'CRE', 'Humanities'),
            ('Agriculture', 'AGR', 'Technicals'),
            ('Business Studies', 'BST', 'Technicals'),
        ]
        subjects = {}
        for name, code, category_name in subjects_data:
            subject = Subject.objects.create(
                school=school,
                name=name,
                code=code,
                category=categories[category_name],
                is_optional=False
            )
            subjects[code] = subject
            self.create_subject_papers(subject)
            self.stdout.write(f'Created subject: {name}')
        return subjects

    def create_subject_papers(self, subject):
        # Most subjects have Paper 1 and Paper 2
        papers = [('1', 100), ('2', 100)]
        for paper_num, max_marks in papers:
            SubjectPaper.objects.create(
                subject=subject,
                paper_number=paper_num,
                max_marks=max_marks,
                student_contribution_marks=50
            )

    def create_form_levels_and_streams(self, school):
        form_levels = {}
        streams = {}
        for form_num in range(1, 5):
            form_level = FormLevel.objects.create(
                school=school,
                number=form_num
            )
            form_levels[form_num] = form_level

            # From data, streams are East and West for Form 2
            stream_names = ['East', 'West'] if form_num == 2 else ['East', 'West', 'North', 'South']
            for stream_name in stream_names:
                stream = Stream.objects.create(
                    school=school,
                    form_level=form_level,
                    name=stream_name
                )
                streams[f'{form_num}_{stream_name}'] = stream
                self.stdout.write(f'Created Stream: Form {form_num} {stream_name}')
        return form_levels, streams

    def create_grading_system(self, school):
        grading_system = GradingSystem.objects.create(
            name='KCSE Grading System',
            school=school,
            is_active=True,
            is_default=True
        )

        # Grading ranges based on typical KCSE system
        ranges_data = [
            (81, 100, 'A', 12),
            (74, 80, 'A-', 11),
            (67, 73, 'B+', 10),
            (60, 66, 'B', 9),
            (53, 59, 'B-', 8),
            (46, 52, 'C+', 7),
            (39, 45, 'C', 6),
            (32, 38, 'C-', 5),
            (25, 31, 'D+', 4),
            (18, 24, 'D', 3),
            (11, 17, 'D-', 2),
            (0, 10, 'E', 1),
        ]

        for min_marks, max_marks, grade, points in ranges_data:
            GradingRange.objects.create(
                grading_system=grading_system,
                min_marks=min_marks,
                max_marks=max_marks,
                grade=grade,
                points=points
            )

        self.stdout.write('Created KCSE grading system')
        return grading_system

    def create_roles(self):
        roles_data = [
            ('Teacher', 'Subject teacher'),
            ('Class Teacher', 'Form class teacher'),
            ('Principal', 'School principal'),
        ]
        roles = {}
        for name, description in roles_data:
            role = Role.objects.create(
                name=name,
                description=description
            )
            roles[name] = role
        return roles

    def create_teacher_groups(self, school):
        groups_data = [
            ('CLASS TEACHERS', 'Class teachers'),
            ('HUMANITIES', 'Humanities teachers'),
            ('LANGUAGES', 'Language teachers'),
            ('MATHS', 'Mathematics teachers'),
            ('SCIENCE', 'Science teachers'),
            ('TECHNICALS', 'Technical subjects teachers'),
        ]
        groups = {}
        for name, description in groups_data:
            group = TeacherGroup.objects.create(
                name=name,
                school=school,
                description=description
            )
            groups[name] = group
            self.stdout.write(f'Created teacher group: {name}')
        return groups

    def populate_teachers(self, school, roles, teacher_groups, subjects):
        teachers_file = os.path.join('system_supportives', 'teachers_list.txt')
        teachers = {}

        with open(teachers_file, 'r') as f:
            lines = f.readlines()[7:]  # Skip header

            for line in lines:
                if line.strip():
                    parts = line.strip().split(',')
                    if len(parts) >= 7:
                        surname = parts[1].strip()
                        first_name = parts[2].strip()
                        other_names = parts[3].strip() if parts[3].strip() else ''
                        username = parts[4].strip()
                        phone = parts[5].strip()
                        gender = parts[6].strip()

                        full_name = f"{first_name} {surname}"
                        if other_names:
                            full_name += f" {other_names}"

                        user = User.objects.create_user(
                            username=username,
                            first_name=first_name,
                            last_name=f"{surname} {other_names}".strip(),
                            email=username.replace('@kikaiboys', '@kikaiboys.school'),
                            password='password123',
                            school=school
                        )

                        user.profile.roles.add(roles['Teacher'])
                        user.profile.phone_number = phone
                        user.profile.save()

                        teachers[username] = user
                        self.stdout.write(f'Created teacher: {full_name}')

                        # Assign to groups and subjects
                        self.assign_teacher_to_groups_and_subjects(user, username, teacher_groups, subjects)

        return teachers

    def assign_teacher_to_groups_and_subjects(self, teacher, username, teacher_groups, subjects):
        # Based on the data, assign teachers to groups and subjects
        assignments = {
            'amiraamara': {'groups': ['LANGUAGES'], 'subjects': ['English']},
            'andrewasiba': {'groups': ['SCIENCE'], 'subjects': ['Biology', 'Chemistry']},
            'biketiclerkson': {'groups': ['HUMANITIES'], 'subjects': ['History and Government']},
            'charlesbwanyonyi': {'groups': ['SCIENCE'], 'subjects': ['Chemistry']},
            'christinewekesa': {'groups': ['HUMANITIES'], 'subjects': ['Christian Religious Education']},
            'fastinewafula': {'groups': ['TECHNICALS'], 'subjects': ['Agriculture']},
            'kevinsakula': {'groups': ['TECHNICALS'], 'subjects': ['Computer Studies']},
            'msimion': {'groups': ['SCIENCE'], 'subjects': ['Physics']},
            'masafuwafula': {'groups': ['CLASS TEACHERS'], 'subjects': []},
            'paulinyangala': {'groups': ['SCIENCE'], 'subjects': ['Biology']},
            'paulwanduyu': {'groups': ['HUMANITIES'], 'subjects': ['Geography']},
            'samuelmaina': {'groups': ['MATHS'], 'subjects': ['Mathematics']},
            'saulkutuyi': {'groups': ['LANGUAGES'], 'subjects': ['Kiswahili']},
        }

        if username in assignments:
            data = assignments[username]

            # Assign to groups
            for group_name in data['groups']:
                if group_name in teacher_groups:
                    TeacherGroupMembership.objects.get_or_create(
                        teacher=teacher,
                        group=teacher_groups[group_name]
                    )
                    self.stdout.write(f'Assigned {teacher.get_full_name()} to group {group_name}')

            # Assign subjects
            for subject_name in data['subjects']:
                subject = Subject.objects.filter(school=teacher.school, name=subject_name).first()
                if subject:
                    TeacherSubject.objects.get_or_create(
                        teacher=teacher,
                        subject=subject
                    )
                    self.stdout.write(f'Assigned {teacher.get_full_name()} to teach {subject_name}')

    def create_students_and_exam_results(self, school, form_levels, subjects, grading_system):
        # Create students from exam results (Form 3) and populate results
        exam = Exam.objects.create(
            school=school,
            name='Form 3 - MID YEAR EXAM',
            form_level=3,
            year=2025,
            term=2,
            is_active=True,
            is_published=True
        )

        results_file = os.path.join('system_supportives', 'exam_results_csv.txt')
        students = {}

        with open(results_file, 'r') as f:
            lines = f.readlines()[7:]  # Skip headers

            for line in lines:
                if line.strip():
                    parts = line.strip().split(',')
                    if len(parts) >= 20:
                        admission_number = parts[0].strip()
                        name = parts[1].strip()
                        stream = parts[2].strip()

                        # Create student if not exists
                        if admission_number not in students:
                            student = Student.objects.create(
                                school=school,
                                name=name,
                                admission_number=admission_number,
                                form_level=form_levels[3],  # Form 3
                                stream=stream,
                                phone_contact='',  # No contact in exam file
                                kcpe_marks=None
                            )
                            students[admission_number] = student
                            self.stdout.write(f'Created student: {name} (Form 3 {stream})')
                        else:
                            student = students[admission_number]

                        # Subject marks
                        subject_marks = {
                            'ENG': parts[3].strip(),
                            'KIS': parts[4].strip(),
                            'MAT': parts[5].strip(),
                            'BIO': parts[6].strip(),
                            'PHY': parts[7].strip(),
                            'CHE': parts[8].strip(),
                            'HIS': parts[9].strip(),
                            'GEO': parts[10].strip(),
                            'CRE': parts[11].strip(),
                            'AGR': parts[12].strip(),
                            'BST': parts[13].strip(),
                        }

                        total_marks = 0
                        total_points = 0
                        subject_count = 0

                        for code, marks_str in subject_marks.items():
                            if marks_str and marks_str != 'X':
                                try:
                                    marks = float(marks_str)
                                    subject = subjects[code]
                                    grade, points = grading_system.get_grade_and_points(marks)

                                    ExamResult.objects.create(
                                        exam=exam,
                                        student=student,
                                        subject=subject,
                                        final_marks=marks,
                                        grade=grade,
                                        points=points
                                    )

                                    total_marks += marks
                                    total_points += points
                                    subject_count += 1

                                except ValueError:
                                    continue

                        if subject_count > 0:
                            mean_marks = total_marks / subject_count
                            mean_points = total_points / subject_count

                            StudentExamSummary.objects.create(
                                exam=exam,
                                student=student,
                                total_marks=total_marks,
                                mean_marks=mean_marks,
                                mean_grade=grading_system.get_grade_and_points(mean_marks)[0],
                                total_points=total_points,
                                stream_position=0,  # Will calculate later
                                overall_position=0,  # Will calculate later
                                subjects_count=subject_count
                            )

                            self.stdout.write(f'Created exam results for: {name}')

        self.stdout.write('Created students and exam results')