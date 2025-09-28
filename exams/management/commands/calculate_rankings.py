from django.core.management.base import BaseCommand
from exams.models import Exam
from exams.services import GradingService

class Command(BaseCommand):
    help = 'Calculate rankings and merit lists for all exams using best of 7 subjects logic'

    def add_arguments(self, parser):
        parser.add_argument('--exam-id', type=int, help='Specific exam ID to recalculate')

    def handle(self, *args, **options):
        if options['exam_id']:
            # Calculate for specific exam
            try:
                exam = Exam.objects.get(id=options['exam_id'])
                GradingService.bulk_calculate_exam_summaries(exam)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully calculated rankings for exam {exam.name}')
                )
            except Exam.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Exam {options["exam_id"]} not found')
                )
        else:
            # Calculate for all active exams
            exams = Exam.objects.filter(is_active=True)
            for exam in exams:
                GradingService.bulk_calculate_exam_summaries(exam)
                self.stdout.write(f'Calculated rankings for {exam.name}')

            self.stdout.write(
                self.style.SUCCESS(f'Successfully calculated rankings for {exams.count()} exams')
            )