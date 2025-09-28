from django.core.management.base import BaseCommand
from django.core.serializers import serialize
import json
import os
from school.models import School

class Command(BaseCommand):
    help = 'Backup data for all schools'

    def add_arguments(self, parser):
        parser.add_argument('--school', type=str, help='School name to backup (optional, backups all if not specified)')
        parser.add_argument('--output', type=str, default='backups', help='Output directory')

    def handle(self, *args, **options):
        school_name = options['school']
        output_dir = options['output']

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if school_name:
            try:
                school = School.objects.get(name=school_name)
                schools = [school]
            except School.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'School "{school_name}" not found'))
                return
        else:
            schools = School.objects.all()

        for school in schools:
            self.backup_school(school, output_dir)

    def backup_school(self, school, output_dir):
        school_dir = os.path.join(output_dir, school.name.replace(' ', '_'))
        if not os.path.exists(school_dir):
            os.makedirs(school_dir)

        # Backup related data
        models_to_backup = [
            ('school.School', [school]),
            ('school.FormLevel', school.form_levels.all()),
            ('school.Stream', school.streams.all()),
            ('subjects.SubjectCategory', school.subjectcategory_set.all()),
            ('subjects.Subject', school.subjects.all()),
            ('subjects.SubjectPaper', school.subjectpaper_set.all()),
            ('accounts.CustomUser', school.users.all()),
            ('students.Student', school.students.all()),
            ('exams.Exam', school.exams.all()),
            ('exams.ExamResult', school.examresult_set.all()),
            ('exams.PaperResult', school.paperresult_set.all()),
            ('exams.StudentExamSummary', school.exam_summaries.all()),
            ('exams.GradingSystem', school.grading_systems.all()),
            ('exams.GradingRange', school.gradingrange_set.all()),
            ('reports.Report', school.report_set.all()),
        ]

        for app_model, queryset in models_to_backup:
            if queryset.exists():
                data = serialize('json', queryset, indent=2)
                filename = f"{app_model.replace('.', '_')}.json"
                filepath = os.path.join(school_dir, filename)
                with open(filepath, 'w') as f:
                    f.write(data)
                self.stdout.write(f'Backed up {app_model} to {filepath}')

        self.stdout.write(self.style.SUCCESS(f'Backup completed for {school.name}'))