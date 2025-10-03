from django.core.management.base import BaseCommand
from students.models import Student
from school.models import School, FormLevel
from django.contrib.auth import get_user_model
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create 5 sample students in each stream (E, S, W, N) across all forms (1-4)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample students...'))

        # Get or create a default school
        school, created = School.objects.get_or_create(
            name='Default School',
            defaults={
                'location': 'Default Location',
                'address': 'Default Address',
                'phone_number': '+254700000000',
                'email': 'school@example.com'
            }
        )
        if created:
            self.stdout.write('Created default school')

        # Create form levels if they don't exist
        form_levels = {}
        for level in range(1, 5):
            form_level, created = FormLevel.objects.get_or_create(
                number=level,
                defaults={'school': school}
            )
            form_levels[level] = form_level
            if created:
                self.stdout.write(f'Created Form Level {level}')

        streams = ['East', 'South', 'West', 'North']
        first_names = [
            'John', 'Mary', 'James', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
            'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Margaret',
            'Thomas', 'Dorothy', 'Charles', 'Lisa', 'Daniel', 'Nancy', 'Matthew', 'Karen',
            'Anthony', 'Betty', 'Mark', 'Helen', 'Donald', 'Sandra', 'Steven', 'Donna'
        ]
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker'
        ]

        admission_no = 1000  # Starting admission number
        total_created = 0

        for form_level_num in range(1, 5):
            form_level_obj = form_levels[form_level_num]
            for stream in streams:
                for i in range(5):  # 5 students per stream
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    full_name = f"{first_name} {last_name}"

                    # Generate random KCPE marks between 200-400
                    kcpe_marks = random.randint(200, 400)

                    student, created = Student.objects.get_or_create(
                        admission_number=str(admission_no),
                        defaults={
                            'name': full_name,
                            'school': school,
                            'form_level': form_level_obj,
                            'stream': stream,
                            'kcpe_marks': kcpe_marks,
                        }
                    )
                    if created:
                        self.stdout.write(f'Created Form {form_level_num} {stream} student: {full_name} ({admission_no})')
                        total_created += 1
                    admission_no += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {total_created} sample students!'))