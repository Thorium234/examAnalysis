import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Student, StudentAdvancement

def process_advancement_spreadsheet(file, academic_year, created_by):
    """
    Process student advancement data from Excel spreadsheet.
    Expected columns:
    - Admission Number
    - Current Form
    - Current Stream
    - Next Form
    - Next Stream
    - Status
    - Remarks (optional)
    """
    try:
        df = pd.read_excel(file)
        required_columns = [
            'Admission Number', 'Current Form', 'Current Stream',
            'Next Form', 'Next Stream', 'Status'
        ]
        
        # Validate columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Clean up data
        df = df.fillna({'Remarks': ''})
        
        # Validate status values
        valid_statuses = dict(StudentAdvancement.ADVANCEMENT_STATUS).keys()
        invalid_statuses = df[~df['Status'].str.lower().isin(valid_statuses)]['Status'].unique()
        if len(invalid_statuses) > 0:
            raise ValidationError(
                f"Invalid status values found: {', '.join(invalid_statuses)}. "
                f"Valid values are: {', '.join(valid_statuses)}"
            )

        # Process records
        advancements_to_create = []
        students_to_update = []
        
        with transaction.atomic():
            for _, row in df.iterrows():
                try:
                    student = Student.objects.get(
                        admission_number=row['Admission Number']
                    )
                except Student.DoesNotExist:
                    raise ValidationError(f"Student with admission number {row['Admission Number']} does not exist.")
                
                status = row['Status'].lower()

                # Validate form level
                current_form = int(row['Current Form'])
                if student.form_level != current_form:
                    raise ValidationError(
                        f"Mismatched form level for student {student.admission_number}. "
                        f"Expected {student.form_level}, but file says {current_form}."
                    )
                
                advancement = StudentAdvancement(
                    student=student,
                    academic_year=academic_year,
                    current_form=current_form,
                    current_stream=student.stream,
                    next_form=int(row['Next Form']),
                    next_stream=row['Next Stream'],
                    status=status,
                    remarks=row['Remarks'],
                    created_by=created_by
                )
                advancements_to_create.append(advancement)

                # Update student's form and stream if promoted/retained
                if status in ['promoted', 'retained']:
                    student.form_level = int(row['Next Form'])
                    student.stream = row['Next Stream']
                    student.is_active = True
                elif status in ['graduated', 'transferred']:
                    student.is_active = False

                students_to_update.append(student)

            StudentAdvancement.objects.bulk_create(advancements_to_create)
            Student.objects.bulk_update(students_to_update, ['form_level', 'stream', 'is_active'])

        return len(advancements_to_create)
    except Exception as e:
        raise ValidationError(f"Error processing spreadsheet: {e}")
