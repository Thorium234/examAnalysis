import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction
from ..models import Student, StudentAdvancement

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
        records_processed = 0
        errors = []
        
        with transaction.atomic():
            for _, row in df.iterrows():
                try:
                    # Get student
                    student = Student.objects.get(
                        admission_number=str(row['Admission Number']).strip()
                    )
                    
                    # Create advancement record
                    advancement = StudentAdvancement(
                        student=student,
                        academic_year=academic_year,
                        current_form=int(row['Current Form']),
                        current_stream=row['Current Stream'],
                        next_form=int(row['Next Form']),
                        next_stream=row['Next Stream'],
                        status=row['Status'].lower(),
                        remarks=row['Remarks'],
                        created_by=created_by
                    )
                    
                    # Validate the record
                    advancement.full_clean()
                    advancement.save()
                    records_processed += 1
                    
                except Student.DoesNotExist:
                    errors.append(f"Student with admission number {row['Admission Number']} not found")
                except ValidationError as e:
                    errors.append(f"Validation error for {row['Admission Number']}: {e}")
                except Exception as e:
                    errors.append(f"Error processing {row['Admission Number']}: {str(e)}")
        
        return {
            'success': len(errors) == 0,
            'records_processed': records_processed,
            'errors': errors
        }
        
    except Exception as e:
        raise ValidationError(f"Error processing spreadsheet: {str(e)}")

def generate_advancement_template():
    """
    Generate a template Excel file for student advancement data.
    """
    columns = [
        'Admission Number',
        'Current Form',
        'Current Stream',
        'Next Form',
        'Next Stream',
        'Status',
        'Remarks'
    ]
    
    df = pd.DataFrame(columns=columns)
    
    # Create a writer object
    output = pd.ExcelWriter('advancement_template.xlsx', engine='openpyxl')
    
    # Write the template
    df.to_excel(output, index=False)
    
    # Add data validation for Status column
    worksheet = output.sheets['Sheet1']
    status_values = [status[1] for status in StudentAdvancement.ADVANCEMENT_STATUS]
    
    # Add validation to Status column (column F, 1-based index)
    status_validation = worksheet.data_validation(
        'F2:F1048576',  # Apply to all rows in Status column
        {
            'validate': 'list',
            'source': status_values
        }
    )
    
    # Set column widths
    for i, column in enumerate(columns):
        worksheet.column_dimensions[chr(65 + i)].width = 15
        
    output.close()
    return output