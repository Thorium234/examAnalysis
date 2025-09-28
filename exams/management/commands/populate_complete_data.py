from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from school.models import School, FormLevel, Stream
from students.models import Student
from subjects.models import Subject, SubjectCategory, SubjectPaper
from accounts.models import Role, Profile, TeacherSubject, TeacherClass
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with complete data structure: forms, streams, students, subjects, and teachers'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate complete data...'))

        # Get or create school
        school = self.get_or_create_school()

        # Create subject categories and subjects
        self.create_subjects(school)

        # Create form levels and streams
        self.create_form_levels_and_streams(school)

        # Create roles
        self.create_roles()

        # Create teachers
        self.create_teachers(school)

        # Create students
        self.create_students(school)

        self.stdout.write(self.style.SUCCESS('Complete data population completed!'))

    def get_or_create_school(self):
        school, created = School.objects.get_or_create(
            name='Friends Kikai Boys High School',
            defaults={
                'location': 'Kikai, Kenya',
                'address': 'P.O. Box 123, Kikai',
                'phone_number': '+254700000000',
                'email': 'info@kikaiboys.school'
            }
        )
        if created:
            self.stdout.write(f'Created school: {school.name}')
        else:
            self.stdout.write(f'Using existing school: {school.name}')
        return school

    def create_subjects(self, school):
        # Create subject categories
        categories_data = [
            ('Languages', 'Language subjects'),
            ('Sciences', 'Science subjects'),
            ('Mathematics', 'Mathematics subject'),
            ('Humanities', 'Humanities subjects'),
            ('Technical', 'Technical subjects'),
        ]

        categories = {}
        for name, description in categories_data:
            category, created = SubjectCategory.objects.get_or_create(
                name=name,
                school=school,
                defaults={'description': description}
            )
            categories[name] = category
            if created:
                self.stdout.write(f'Created subject category: {name}')

        # Create subjects
        subjects_data = [
            ('English', 'ENG', 'Languages'),
            ('Kiswahili', 'KIS', 'Languages'),
            ('Mathematics', 'MAT', 'Mathematics'),
            ('Biology', 'BIO', 'Sciences'),
            ('Physics', 'PHY', 'Sciences'),
            ('Chemistry', 'CHE', 'Sciences'),
            ('History and Government', 'HIS', 'Humanities'),
            ('Geography', 'GEO', 'Humanities'),
            ('Christian Religious Education', 'CRE', 'Humanities'),
            ('Agriculture', 'AGR', 'Technical'),
            ('Business Studies', 'BST', 'Technical'),
            ('Computer Studies', 'COM', 'Technical'),
        ]

        for name, code, category_name in subjects_data:
            subject, created = Subject.objects.get_or_create(
                school=school,
                name=name,
                defaults={
                    'code': code,
                    'category': categories[category_name],
                    'is_optional': False
                }
            )
            if created:
                self.create_subject_papers(subject)
                self.stdout.write(f'Created subject: {name}')

    def create_subject_papers(self, subject):
        # Define papers based on subject
        if subject.name in ['English', 'Kiswahili']:
            papers = [
                ('Paper 1', 60),
                ('Paper 2', 80),
                ('Paper 3', 60),
            ]
        elif subject.name in ['Biology', 'Physics', 'Chemistry']:
            papers = [
                ('Paper 1', 80),
                ('Paper 2', 80),
                ('Paper 3', 40),
            ]
        elif subject.name == 'Mathematics':
            papers = [
                ('Paper 1', 100),
                ('Paper 2', 100),
            ]
        else:
            papers = [
                ('Paper 1', 100),
                ('Paper 2', 100),
            ]

        for paper_name, max_marks in papers:
            paper_number = int(paper_name.split()[-1])
            SubjectPaper.objects.get_or_create(
                subject=subject,
                paper_number=paper_number,
                defaults={
                    'max_marks': max_marks,
                    'student_contribution_marks': 100 // len(papers)
                }
            )

    def create_form_levels_and_streams(self, school):
        streams = ['East', 'West', 'North', 'South']

        for form_num in range(1, 5):
            form_level, created = FormLevel.objects.get_or_create(
                school=school,
                number=form_num
            )
            if created:
                self.stdout.write(f'Created Form Level: {form_level}')

            for stream_name in streams:
                stream, created = Stream.objects.get_or_create(
                    school=school,
                    form_level=form_level,
                    name=stream_name
                )
                if created:
                    self.stdout.write(f'Created Stream: {stream}')

    def create_roles(self):
        roles_data = [
            ('Principal', 'School principal'),
            ('Deputy Principal', 'Deputy principal'),
            ('Teacher', 'Subject teacher'),
            ('Class Teacher', 'Form class teacher'),
        ]

        for name, description in roles_data:
            role, created = Role.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'Created role: {name}')

    def create_teachers(self, school):
        # Kenyan teacher names
        teachers_data = [
            ('john_doe', 'John Doe', 'Principal'),
            ('jane_smith', 'Jane Smith', 'Deputy Principal'),
            ('amira_amara', 'Amira Amara', 'Teacher'),
            ('biketi_clerkson', 'Biketi Clerkson', 'Teacher'),
            ('charles_wanyonyi', 'Charles Wanyonyi', 'Teacher'),
            ('christine_wekesa', 'Christine Wekesa', 'Teacher'),
            ('fastine_wafula', 'Fastine Wafula', 'Teacher'),
            ('grace_omondi', 'Grace Omondi', 'Teacher'),
            ('henry_kiprop', 'Henry Kiprop', 'Teacher'),
            ('isaac_mwangi', 'Isaac Mwangi', 'Teacher'),
            ('joyce_njoroge', 'Joyce Njoroge', 'Teacher'),
            ('kennedy_otieno', 'Kennedy Otieno', 'Teacher'),
        ]

        # Subject assignments
        subject_assignments = {
            'amira_amara': ['English'],
            'biketi_clerkson': ['Kiswahili', 'History and Government'],
            'charles_wanyonyi': ['Chemistry'],
            'christine_wekesa': ['Christian Religious Education'],
            'fastine_wafula': ['Agriculture'],
            'grace_omondi': ['Biology'],
            'henry_kiprop': ['Physics'],
            'isaac_mwangi': ['Mathematics'],
            'joyce_njoroge': ['Geography'],
            'kennedy_otieno': ['Business Studies', 'Computer Studies'],
        }

        for username, full_name, role_name in teachers_data:
            first_name, last_name = full_name.rsplit(' ', 1)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f'{username}@kikaiboys.school',
                    'school': school
                }
            )
            if created:
                user.set_password('password123')
                user.save()

                # Assign role
                role = Role.objects.get(name=role_name)
                user.profile.roles.add(role)

                # Assign subjects if teacher
                if role_name == 'Teacher' and username in subject_assignments:
                    for subject_name in subject_assignments[username]:
                        subject = Subject.objects.get(school=school, name=subject_name)
                        TeacherSubject.objects.get_or_create(
                            teacher=user,
                            subject=subject
                        )

                # Assign class teacher roles for some teachers
                if username in ['amira_amara', 'grace_omondi', 'henry_kiprop']:
                    form_num = 2 if username == 'amira_amara' else (3 if username == 'grace_omondi' else 4)
                    stream_name = 'East' if username == 'amira_amara' else ('West' if username == 'grace_omondi' else 'North')
                    form_level = FormLevel.objects.get(school=school, number=form_num)
                    TeacherClass.objects.get_or_create(
                        teacher=user,
                        school=school,
                        form_level=form_num,
                        stream=stream_name,
                        defaults={'is_class_teacher': True}
                    )

                self.stdout.write(f'Created teacher: {full_name} ({role_name})')

    def create_students(self, school):
        # Kenyan student names (mix of common names)
        first_names = [
            'David', 'Michael', 'John', 'James', 'Robert', 'William', 'Joseph', 'Daniel', 'Thomas', 'Andrew',
            'Peter', 'Paul', 'Mark', 'Luke', 'Matthew', 'Simon', 'Stephen', 'Philip', 'Barnabas', 'Timothy',
            'Kevin', 'Brian', 'Chris', 'Dennis', 'Edward', 'Francis', 'George', 'Henry', 'Isaac', 'Jacob',
            'Samuel', 'Benjamin', 'Alexander', 'Nicholas', 'Anthony', 'Charles', 'Richard', 'Patrick', 'Patrick', 'Steven'
        ]

        last_names = [
            'Wanjala', 'Wekesa', 'Kiplagat', 'Kiptoo', 'Cheruiyot', 'Kiprop', 'Rono', 'Kipkoech', 'Langat', 'Bett',
            'Simiyu', 'Masinde', 'Wafula', 'Omondi', 'Oduya', 'Njoroge', 'Mwangi', 'Kariuki', 'Maina', 'Kamau',
            'Otieno', 'Ochieng', 'Adhiambo', 'Achieng', 'Atieno', 'Awino', 'Akinyi', 'Akoth', 'Auma', 'Ayuma',
            'Kilonzo', 'Muli', 'Muthomi', 'Ndungu', 'Njenga', 'Nyaga', 'Mbugua', 'Gichuki', 'Githinji', 'Muriuki'
        ]

        streams = ['East', 'West', 'North', 'South']
        subjects = list(Subject.objects.filter(school=school))

        for form_num in range(1, 5):
            form_level = FormLevel.objects.get(school=school, number=form_num)

            for stream_name in streams:
                stream = Stream.objects.get(school=school, form_level=form_level, name=stream_name)

                for i in range(5):  # 5 students per stream
                    # Generate unique admission number
                    admission_num = f"{form_num}{stream_name[0]}{str(i+1).zfill(2)}"

                    # Generate name
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    full_name = f"{first_name} {last_name}"

                    # Create student
                    student, created = Student.objects.get_or_create(
                        school=school,
                        admission_number=admission_num,
                        defaults={
                            'name': full_name,
                            'form_level': form_level,
                            'stream': stream_name,
                            'kcpe_marks': random.randint(200, 450) if form_num == 1 else None,
                            'phone_contact': f"+2547{random.randint(10000000, 99999999)}"
                        }
                    )

                    if created:
                        # Assign subjects (all subjects for the form level)
                        student.subjects.set(subjects)
                        self.stdout.write(f'Created student: {full_name} (Form {form_num} {stream_name})')