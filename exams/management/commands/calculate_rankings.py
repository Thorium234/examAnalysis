from django.core.management.base import BaseCommand
from exams.models import Exam
from exams.services import ExamResultsService

class Command(BaseCommand):
    help = 'Calculate rankings and merit lists for all exams'

    def add_arguments(self, parser):
        parser.add_argument('--exam-id', type=int, help='Specific exam ID to recalculate')

    def handle(self, *args, **options):
        if options['exam_id']:
            # Calculate for specific exam
            if ExamResultsService.recalculate_exam_rankings(options['exam_id']):
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully calculated rankings for exam {options["exam_id"]}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Exam {options["exam_id"]} not found')
                )
        else:
            # Calculate for all active exams
            exams = Exam.objects.filter(is_active=True)
            for exam in exams:
                ExamResultsService.recalculate_exam_rankings(exam.id)
                self.stdout.write(f'Calculated rankings for {exam.name}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully calculated rankings for {exams.count()} exams')
            )