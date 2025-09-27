from django.core.management.base import BaseCommand
from exams.models import Exam
from school.models import School


class Command(BaseCommand):
    help = 'Create comprehensive exams for all form levels (Form 1-4) for 2025 Term 2'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school',
            type=str,
            help='School name to create exams for (optional, defaults to first school)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting exam creation...'))

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

        self.stdout.write(f'Creating exams for school: {school.name}')

        # Exam details
        exam_names = ['AVERAGE EXAM', 'MID YEAR EXAM', 'END TERM EXAM']
        year = 2025
        term = 2
        form_levels = [1, 2, 3, 4]

        exams_created = 0

        for form_level in form_levels:
            for exam_name in exam_names:
                # Use get_or_create to avoid duplicates
                exam, created = Exam.objects.get_or_create(
                    school=school,
                    name=exam_name,
                    form_level=form_level,
                    year=year,
                    term=term,
                    defaults={'is_published': False}
                )
                if created:
                    exams_created += 1
                    self.stdout.write(f'Created: {exam}')
                else:
                    self.stdout.write(f'Already exists: {exam}')

        self.stdout.write(self.style.SUCCESS(f'Exam creation completed! Created {exams_created} new exams.'))