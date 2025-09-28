from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model 
from students.models import (
    Student, Subject, ClassSubjectAvailability, 
    StudentSubjectEnrollment, SubjectPaper, SubjectPaperRatio
)
from exams.models import (
    Exam, ExamResult, StudentExamSummary,
    SubjectCategory, GradingSystem, GradingRange
)
from school.models import School, FormLevel
from accounts.models import TeacherSubject, TeacherClass
from datetime import date, datetime
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data from Friends Kikai Boys High School'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate sample data...'))
        
        # Create subject categories and grading systems
        self.create_subject_categories()
        
        # Create subjects
        self.create_subjects()
        
        # Create subject papers
        self.create_subject_papers()
        
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

    def create_subject_categories(self):
        categories_data = [
            ('Languages', 'Language subjects including English and Kiswahili'),
            ('Sciences', 'Science subjects including Biology, Chemistry and Physics'),
            ('Mathematics', 'Mathematics subject'),
            ('Humanities', 'Humanities subjects including History, Geography and CRE'),
            ('Technical', 'Technical subjects including Agriculture and Business Studies'),
        ]
        
        # Create categories
        for name, description in categories_data:
            category, created = SubjectCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                # Create default grading system for this category
                grading = GradingSystem.objects.create(
                    name=f'Standard {name} Grading',
                    category=category,
                    is_active=True,
                    is_default=True,
                    created_by=None  # No user yet
                )
                
                # Create grading ranges
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
                
                for low, high, grade, points in ranges_data:
                    GradingRange.objects.create(
                        grading_system=grading,
                        low_mark=low,
                        high_mark=high,
                        grade=grade,
                        points=points
                    )
            
            self.stdout.write(f'Created category: {name}')
    
    def create_subjects(self):
        subjects_data = [
            ('English', 'ENG', 'Languages', 3),
            ('Kiswahili', 'KIS', 'Languages', 3),
            ('Mathematics', 'MAT', 'Mathematics', 2),
            ('Biology', 'BIO', 'Sciences', 3),
            ('Physics', 'PHY', 'Sciences', 3),
            ('Chemistry', 'CHE', 'Sciences', 3),
            ('History and Government', 'HIS', 'Humanities', 2),
            ('Geography', 'GEO', 'Humanities', 2),
            ('Christian Religious Education', 'CRE', 'Humanities', 2),
            ('Agriculture', 'AGR', 'Technical', 2),
            ('Business Studies', 'BST', 'Technical', 2),
            ('Computer Studies', 'COM', 'Technical', 2),
        ]
        
        for name, code, category_name, num_papers in subjects_data:
            category = SubjectCategory.objects.get(name=category_name)
            subject, created = Subject.objects.get_or_create(
                name=name,
                defaults={
                    'code': code,
                    'category': category,
                    'grading_system': category.grading_systems.get(is_default=True)
                }
            )
            if created:
                self.stdout.write(f'Created subject: {name}')
                
    def create_subject_papers(self):
        subjects = Subject.objects.all()
        for subject in subjects:
            # Get number of papers for this subject
            num_papers = len(subject.papers.all())
            if num_papers == 0:
                # Create papers based on subject
                if subject.name in ['English', 'Kiswahili']:
                    papers = [
                        ('Paper 1', 1, 60),  # Language paper
                        ('Paper 2', 2, 80),  # Literature paper
                        ('Paper 3', 3, 60),  # Oral/Creative paper
                    ]
                elif subject.name in ['Biology', 'Physics', 'Chemistry']:
                    papers = [
                        ('Paper 1', 1, 80),  # Theory paper
                        ('Paper 2', 2, 80),  # Theory paper
                        ('Paper 3', 3, 40),  # Practical paper
                    ]
                elif subject.name == 'Mathematics':
                    papers = [
                        ('Paper 1', 1, 100),
                        ('Paper 2', 2, 100),
                    ]
                else:
                    papers = [
                        ('Paper 1', 1, 100),
                        ('Paper 2', 2, 100) if subject.name not in ['Agriculture', 'Business Studies', 'Computer Studies'] else None
                    ]
                    papers = [p for p in papers if p]  # Remove None values
                
                # Create the papers
                for paper_name, paper_number, max_marks in papers:
                    paper = SubjectPaper.objects.create(
                        name=paper_name,
                        paper_number=paper_number,
                        max_marks=max_marks
                    )
                    
                    # Create paper ratio (contribution to final mark)
                    ratio = 100.0 / len(papers)  # Equal weight distribution
                    SubjectPaperRatio.objects.create(
                        subject=subject,
                        paper=paper,
                        student_contribution_marks=ratio
                    )
                
                self.stdout.write(f'Created papers for: {subject.name}')

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
            for stream in ['East', 'West', 'North', 'South']:
                for subject in subjects:
                    ClassSubjectAvailability.objects.get_or_create(
                        form_level=form_level,
                        stream=stream,
                        subject=subject,
                        defaults={'is_available': True}
                    )
        
        self.stdout.write('Created class subjects for all forms and streams')

    def create_exams(self):
        # First ensure we have form levels
        forms = []
        for level in [2, 3]:
            form, _ = FormLevel.objects.get_or_create(number=level, defaults={'school': School.objects.first()})
            forms.append(form)

        # Create sample exams
        exams_data = [
            ('AVERAGE EXAM', 'is_year_average', 2025, 2),
            ('MID YEAR EXAM', 'is_ordinary_exam', 2025, 2),
            ('END TERM EXAM', 'is_ordinary_exam', 2025, 2),
        ]
        
        for name, exam_type, year, term in exams_data:
            exam, created = Exam.objects.get_or_create(
                name=name,
                year=year,
                term=term,
                defaults={
                    exam_type: True,
                    'is_active': True
                }
            )
            if created:
                exam.participating_forms.set(forms)
                self.stdout.write(f'Created exam: {name}')

    def create_exam_results(self):
        # Create sample exam results based on the documents
        
        # Form 2 Average Exam results (from the report documents)
        form2_exam = Exam.objects.get(name='AVERAGE EXAM')
        
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
            # Get paper ratios for the subject
            paper_ratios = SubjectPaperRatio.objects.filter(subject=subject)
            ExamResult.objects.get_or_create(
                exam=form2_exam,
                student=tobias,
                subject=subject,
                status='P',
                defaults={'total_marks': marks}
            )
        
        # Sample results for Gospel Chemuku Walukana (4473)
        gospel = Student.objects.get(admission_number='4473')
        gospel_results = [
            ('English', 68),
            ('Kiswahili', 44),
            ('Mathematics', 7),
            ('Biology', 22),
            ('Physics', 21),
            ('Chemistry', 18),
            ('Geography', 17),
            ('Computer Studies', 6),
            ('Business Studies', 25),
        ]
        
        for subject_name, marks in gospel_results:
            subject = Subject.objects.get(name=subject_name)
            ExamResult.objects.get_or_create(
                exam=form2_exam,
                student=gospel,
                subject=subject,
                status='P',
                defaults={'total_marks': marks}
            )
        
        # Form 3 Mid Year Exam results (sample from merit list)
        form3_exam = Exam.objects.get(name='MID YEAR EXAM')
        
        # Top performer: Gospel Chemuku Walukana (4473)
        gospel_mid_results = [
            ('English', 18),
            ('Kiswahili', 41),
            ('Mathematics', 9),
            ('Biology', 50),
            ('Chemistry', 13),
            ('History and Government', 64),
            ('Christian Religious Education', 78),
            ('Business Studies', 16),
        ]
        
        for subject_name, marks in gospel_mid_results:
            subject = Subject.objects.get(name=subject_name)
            ExamResult.objects.get_or_create(
                exam=form3_exam,
                student=gospel,
                subject=subject,
                status='P',
                defaults={'total_marks': marks}
            )
        
        # Create random results for other students
        students = Student.objects.all()
        subjects = Subject.objects.all()
        exams = Exam.objects.all()
        
        for exam in exams:
            for student in students:
                # Skip if student already has results for this exam
                if ExamResult.objects.filter(exam=exam, student=student).exists():
                    continue
                
                # Create random results for 5-8 subjects per student
                random_subjects = random.sample(list(subjects), random.randint(5, 8))
                for subject in random_subjects:
                    # 85% chance of present, 10% absent, 5% disqualified
                    status = random.choices(['P', 'A', 'D'], weights=[85, 10, 5])[0]
                    
                    if status == 'P':
                        marks = random.randint(15, 85)  # Random marks between 15-85
                    else:
                        marks = -1 if status == 'A' else -2  # -1 for absent, -2 for disqualified
                    
                    ExamResult.objects.get_or_create(
                        exam=exam,
                        student=student,
                        subject=subject,
                        status=status,
                        defaults={'total_marks': marks}
                    )
        
        self.stdout.write('Created exam results for students')