from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from school.models import School, FormLevel, Stream
from students.models import Student
from subjects.models import Subject, SubjectCategory, SubjectPaper
from accounts.models import Role, Profile, TeacherSubject, TeacherClass
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create Bushili Academy school with principal and data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to create Bushili Academy...'))

        # Create school
        school = self.create_school()

        # Create subject categories and subjects
        self.create_subjects(school)

        # Create form levels and streams
        self.create_form_levels_and_streams(school)

        # Create roles
        self.create_roles()

        # Create principal
        self.create_principal(school)

        # Create teachers
        self.create_teachers(school)

        # Create students
        self.create_students(school)

        self.stdout.write(self.style.SUCCESS('Bushili Academy creation completed!'))

    def create_school(self):
        school, created = School.objects.get_or_create(
            name='Bushili Academy',
            defaults={
                'location': 'Bushili, Kenya',
                'address': 'P.O. Box 123, Bushili',
                'phone_number': '+254700000000',
                'email': 'info@bushiliacademy.school'
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
        # 16 streams per form: North1-4, East1-4, South1-4, West1-4
        stream_groups = ['North', 'East', 'South', 'West']
        streams = []
        for group in stream_groups:
            for i in range(1, 5):
                streams.append(f'{group}{i}')

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

    def create_principal(self, school):
        username = 'emmanuelshitotei'
        email = 'emmanuelshitotei@gmail.com'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': 'Emmanuel',
                'last_name': 'Shitotei',
                'email': email,
                'school': school
            }
        )
        if created:
            user.set_password('29980201')
            user.save()

            # Assign role
            role = Role.objects.get(name='Principal')
            user.profile.roles.add(role)

            self.stdout.write(f'Created principal: {user.get_full_name()}')

    def create_teachers(self, school):
        # Some teachers
        teachers_data = [
            ('teacher1', 'John Doe', 'Teacher'),
            ('teacher2', 'Jane Smith', 'Teacher'),
            ('teacher3', 'Bob Johnson', 'Teacher'),
        ]

        subject_assignments = {
            'teacher1': ['English', 'Mathematics'],
            'teacher2': ['Biology', 'Chemistry'],
            'teacher3': ['History and Government', 'Geography'],
        }

        for username, full_name, role_name in teachers_data:
            first_name, last_name = full_name.rsplit(' ', 1)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f'{username}@bushiliacademy.school',
                    'school': school
                }
            )
            if created:
                user.set_password('password123')
                user.save()

                # Assign role
                role = Role.objects.get(name=role_name)
                user.profile.roles.add(role)

                # Assign subjects
                if username in subject_assignments:
                    for subject_name in subject_assignments[username]:
                        subject = Subject.objects.get(school=school, name=subject_name)
                        TeacherSubject.objects.get_or_create(
                            teacher=user,
                            subject=subject
                        )

                self.stdout.write(f'Created teacher: {full_name}')

    def create_students(self, school):
        first_names = [
            'David', 'Michael', 'John', 'James', 'Robert', 'William', 'Joseph', 'Daniel', 'Thomas', 'Andrew',
            'Peter', 'Paul', 'Mark', 'Luke', 'Matthew', 'Simon', 'Stephen', 'Philip', 'Barnabas', 'Timothy',
        ]

        last_names = [
            'Wanjala', 'Wekesa', 'Kiplagat', 'Kiptoo', 'Cheruiyot', 'Kiprop', 'Rono', 'Kipkoech', 'Langat', 'Bett',
        ]

        subjects = list(Subject.objects.filter(school=school))

        for form_num in range(1, 5):
            form_level = FormLevel.objects.get(school=school, number=form_num)
            streams = Stream.objects.filter(school=school, form_level=form_level)

            for stream in streams:
                for i in range(20):  # 20 students per stream
                    admission_num = f"{form_num}{stream.name}{str(i+1).zfill(2)}"

                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    full_name = f"{first_name} {last_name}"

                    student, created = Student.objects.get_or_create(
                        school=school,
                        admission_number=admission_num,
                        defaults={
                            'name': full_name,
                            'form_level': form_level,
                            'stream': stream.name,
                            'kcpe_marks': random.randint(200, 450) if form_num == 1 else None,
                            'phone_contact': f"+2547{random.randint(10000000, 99999999)}"
                        }
                    )

                    if created:
                        student.subjects.set(subjects)
                        self.stdout.write(f'Created student: {full_name} (Form {form_num} {stream.name})')