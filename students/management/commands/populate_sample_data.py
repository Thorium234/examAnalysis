from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from students.models import Student, Subject, ClassSubject, StudentSubject
from exams.models import Exam, ExamResult, StudentExamSummary
from accounts.models import TeacherSubject, TeacherClass
from datetime import date
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data from Friends Kikai Boys High School'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate sample data...'))
        
        # Create subjects
        self.create_subjects()
        
        # Create teachers and users
        self.create_users()
        
        # Create students based on Form 2 class list
        self.create_form2_students()
        
        # Create form 3 students (for merit list)
        self.create_form3_students()
        
        # Create class subjects
        self.create_class_subjects()
        
        # Create exams
        self.create_exams()
        
        # Create exam results
        self.create_exam_results()
        
        self.stdout.write(self.style.SUCCESS('Sample data population completed!'))

    def create_subjects(self):
        subjects_data = [
            ('English', 'ENG'),
            ('Kiswahili', 'KIS'),
            ('Mathematics', 'MAT'),
            ('Biology', 'BIO'),
            ('Physics', 'PHY'),
            ('Chemistry', 'CHE'),
            ('History and Government', 'HIS'),
            ('Geography', 'GEO'),
            ('Christian Religious Education', 'CRE'),
            ('Agriculture', 'AGR'),
            ('Business Studies', 'BST'),
            ('Computer Studies', 'COM'),
        ]
        
        for name, code in subjects_data:
            subject, created = Subject.objects.get_or_create(name=name, code=code)
            if created:
                self.stdout.write(f'Created subject: {name}')

    def create_users(self):
        # Create school administrators
        users_data = [
            ('principal', 'John Doe', 'Principal', 'principal'),
            ('deputy', 'Jane Smith', 'Deputy Principal', 'deputy'),
            ('dos', 'Peter Johnson', 'Director of Studies', 'dos'),
            ('amira_amara', 'Amira Amara', 'Class Teacher Form 2', 'teacher'),
            ('biketi_clerkson', 'Biketi Clerkson', 'Kiswahili Teacher', 'teacher'),
            ('charles_wanyonyi', 'Charles B. Wanyonyi', 'Chemistry Teacher', 'teacher'),
            ('christine_wekesa', 'Christine Wekesa', 'CRE Teacher', 'teacher'),
            ('fastine_wafula', 'Fastine Wafula', 'Agriculture Teacher', 'teacher'),
        ]
        
        for username, full_name, description, role in users_data:
            first_name, last_name = full_name.split(' ', 1)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f'{username}@kikaiboys.school',
                    'role': role,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {username} ({description})')

        # Assign subjects to teachers
        teacher_subjects = [
            ('amira_amara', 'English'),
            ('biketi_clerkson', 'Kiswahili'),
            ('biketi_clerkson', 'History and Government'),
            ('charles_wanyonyi', 'Chemistry'),
            ('christine_wekesa', 'Christian Religious Education'),
            ('fastine_wafula', 'Agriculture'),
        ]
        
        for username, subject_name in teacher_subjects:
            user = User.objects.get(username=username)
            teacher_subject, created = TeacherSubject.objects.get_or_create(
                teacher=user,
                subject_name=subject_name
            )
            if created:
                self.stdout.write(f'Assigned {subject_name} to {username}')

        # Assign class to class teacher
        amira = User.objects.get(username='amira_amara')
        TeacherClass.objects.get_or_create(
            teacher=amira,
            form_level=2,
            stream='West',
            is_class_teacher=True
        )
        TeacherClass.objects.get_or_create(
            teacher=amira,
            form_level=2,
            stream='East',
            is_class_teacher=False
        )

    def create_form2_students(self):
        # Form 2 students from the class list document
        form2_students = [
            (71, 'Masinde Hillary', 'West', None),
            (4399, 'Wanyonyi Ebysai', 'East', None),
            (4400, 'Rex Simiyu', 'West', None),
            (4401, 'Daniel Simiyu', 'East', None),
            (4402, 'Samson Kiptrotich', 'West', None),
            (4403, 'Joshua Kiplagat', 'East', None),
            (4404, 'Brian Wanjala', 'West', None),
            (4405, 'Brarly Kimatia', 'East', None),
            (4406, 'Elly Tarogon', 'West', None),
            (4407, 'Luis Simiyu Wanjala', 'East', None),
            (4408, 'Haggai Kiptrotich', 'West', None),
            (4410, 'Kilongi Deninnis Wangila', 'West', None),
            (4411, 'Morgan Surai Kipsambu', 'East', None),
            (4412, 'Job Wekesa', 'West', None),
            (4413, 'Yonali Kipling At Masai', 'East', None),
            (4415, 'Brighton Wanjala', 'East', None),
            (4416, 'Samwell Kibet', 'West', None),
            (4417, 'Kibet Ndiema Allan', 'East', None),
            (4418, 'Bravin Kiptoo', 'East', None),
            (4419, 'Seith Osiya', 'East', None),
            (4420, 'John Lagasta', 'West', None),
            (4421, 'Bravine Wekesa', 'East', None),
            (4422, 'Morgan Rotich', 'West', None),
            (4424, 'Allan Kipsang', 'West', None),
            (4425, 'Gasper Wafula', 'West', 298),
            (4467, 'Tobias Juma', 'West', None),  # From the exam report
            (4456, 'Kibet Morgan', 'West', None),  # From the exam report
            (44770, 'W. Jesse Mabonga', 'West', None),  # From the exam report
        ]
        
        for admission_no, name, stream, kcpe in form2_students:
            student, created = Student.objects.get_or_create(
                admission_number=str(admission_no),
                defaults={
                    'name': name,
                    'form_level': 2,
                    'stream': stream,
                    'kcpe_marks': kcpe,
                }
            )
            if created:
                self.stdout.write(f'Created Form 2 student: {name} ({admission_no})')

    def create_form3_students(self):
        # Form 3 students from merit list
        form3_students = [
            (4473, 'Gospel Chemuku Walukana', 'East', None),
            (4323, 'Cornelius Wekesa Mayam A', 'West', None),
            (4324, 'Mordecai Mayamba', 'East', None),
            (4307, 'Abraham Kiplagat Ndiwa', 'East', None),
            (4303, 'Muliro W Nickson', 'East', None),
            (4335, 'Micah Wanyonyi Wafula', 'East', None),
            (4356, 'Simiyu Gideon Wasike', 'East', None),
            (4341, 'Wanjala Moses Wekesa', 'East', None),
            (4496, 'Omanyala Bramuel', 'East', None),
            (4503, 'Barasa Malisha Joshua', 'West', None),
            (4325, 'Masinde Mark Sikuku', 'West', None),
            (4501, 'Clinton Barasa', 'West', 200),
        ]
        
        for admission_no, name, stream, kcpe in form3_students:
            student, created = Student.objects.get_or_create(
                admission_number=str(admission_no),
                defaults={
                    'name': name,
                    'form_level': 3,
                    'stream': stream,
                    'kcpe_marks': kcpe,
                }
            )
            if created:
                self.stdout.write(f'Created Form 3 student: {name} ({admission_no})')

    def create_class_subjects(self):
        # Create class subjects for Form 2 and Form 3
        subjects = Subject.objects.all()
        
        for form_level in [2, 3]:
            for stream in ['East', 'West']:
                for subject in subjects:
                    max_marks = 100  # Default maximum marks
                    ClassSubject.objects.get_or_create(
                        form_level=form_level,
                        stream=stream,
                        subject=subject,
                        defaults={'maximum_marks': max_marks}
                    )
        
        self.stdout.write('Created class subjects for all forms and streams')

    def create_exams(self):
        # Create sample exams
        exams_data = [
            ('AVERAGE EXAM', 'AVERAGE', 2025, 2, 2),
            ('MID YEAR EXAM', 'MID_YEAR', 2025, 2, 3),
            ('END TERM EXAM', 'END_TERM', 2025, 2, 2),
        ]
        
        for name, exam_type, year, term, form_level in exams_data:
            exam, created = Exam.objects.get_or_create(
                name=name,
                exam_type=exam_type,
                year=year,
                term=term,
                form_level=form_level
            )
            if created:
                self.stdout.write(f'Created exam: {name} - Form {form_level}')

    def create_exam_results(self):
        # Create sample exam results based on the documents
        
        # Form 2 Average Exam results (from the report documents)
        form2_exam = Exam.objects.get(name='AVERAGE EXAM', form_level=2)
        
        # Sample results for Tobias Juma (4467)
        tobias = Student.objects.get(admission_number='4467')
        tobias_results = [
            ('English', 31),
            ('Kiswahili', 52),
            ('Mathematics', 20),
            ('Biology', 22),
            ('Chemistry', 9),
            ('Geography', 25),
            ('Christian Religious Education', 25),
            ('Agriculture', 39),
        ]
        
        for subject_name, marks in tobias_results:
            subject = Subject.objects.get(name=subject_name)
            ExamResult.objects.get_or_create(
                exam=form2_exam,
                student=tobias,
                subject=subject,
                defaults={'marks': marks}
            )
        
        # Sample results for Kibet Morgan (4456)
        kibet = Student.objects.get(admission_number='4456')
        kibet_results = [
            ('English', 37),
            ('Kiswahili', 44),
            ('Mathematics', 7),
            ('Biology', 22),
            ('Physics', 21),
            ('Chemistry', 18),
            ('Geography', 17),
            ('Computer Studies', 6),
            ('Business Studies', 25),
        ]
        
        for subject_name, marks in kibet_results:
            subject = Subject.objects.get(name=subject_name)
            ExamResult.objects.get_or_create(
                exam=form2_exam,
                student=kibet,
                subject=subject,
                defaults={'marks': marks}
            )
        
        # Form 3 Mid Year Exam results (sample from merit list)
        form3_exam = Exam.objects.get(name='MID YEAR EXAM', form_level=3)
        
        # Top performer: Gospel Chemuku Walukana (4473)
        gospel = Student.objects.get(admission_number='4473')
        gospel_results = [
            ('English', 18),
            ('Kiswahili', 41),
            ('Mathematics', 9),
            ('Biology', 50),
            ('Chemistry', 13),
            ('History and Government', 64),
            ('Christian Religious Education', 78),
            ('Business Studies', 16),
        ]
        
        for subject_name, marks in gospel_results:
            subject = Subject.objects.get(name=subject_name)
            ExamResult.objects.get_or_create(
                exam=form3_exam,
                student=gospel,
                subject=subject,
                defaults={'marks': marks}
            )
        
        # Create random results for other students
        students = Student.objects.all()
        subjects = Subject.objects.all()
        exams = Exam.objects.all()
        
        for exam in exams:
            form_students = Student.objects.filter(form_level=exam.form_level)
            for student in form_students:
                # Skip if already has results
                if ExamResult.objects.filter(exam=exam, student=student).exists():
                    continue
                
                # Create random results for 5-8 subjects per student
                random_subjects = random.sample(list(subjects), random.randint(5, 8))
                for subject in random_subjects:
                    marks = random.randint(15, 85)  # Random marks between 15-85
                    ExamResult.objects.get_or_create(
                        exam=exam,
                        student=student,
                        subject=subject,
                        defaults={'marks': marks}
                    )
        
        self.stdout.write('Created exam results for students')