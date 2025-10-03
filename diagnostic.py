from school.models import FormLevel, Stream
from students.models import Student

print("=" * 60)
print("DIAGNOSTIC CHECK FOR SCHOOL DASHBOARD DATA")
print("=" * 60)

# Check FormLevels
print("\n1. FORM LEVELS:")
print("-" * 40)
form_levels = FormLevel.objects.all()
print(f"Total Form Levels: {form_levels.count()}")
for form in form_levels:
    print(f"\n  Form {form.number} (ID: {form.id})")
    print(f"    - {form}")

# Check Streams
print("\n\n2. STREAMS:")
print("-" * 40)
streams = Stream.objects.all()
print(f"Total Streams: {streams.count()}")
for stream in streams:
    print(f"\n  {stream.name} (ID: {stream.id})")
    print(f"    - Form Level: {stream.form_level}")
    print(f"    - Form Level ID: {stream.form_level_id}")

# Check Students
print("\n\n3. STUDENTS:")
print("-" * 40)
students = Student.objects.all()
print(f"Total Students: {students.count()}")
for student in students[:5]:  # Show first 5
    print(f"\n  {student.admission_number} - {student.name}")
    print(f"    - Stream: {student.stream}")
    print(f"    - Form Level: {student.form_level}")

# Check relationships
print("\n\n4. RELATIONSHIP CHECKS:")
print("-" * 40)
for form in form_levels:
    # Check streams related to this form
    form_streams = Stream.objects.filter(form_level=form)
    print(f"\n  Form {form.number}:")
    print(f"    - Streams: {form_streams.count()}")
    
    # Check students for this form
    student_count = Student.objects.filter(form_level=form).count()
    print(f"    - Total Students: {student_count}")

# Check if reverse relationships work
print("\n\n5. REVERSE RELATIONSHIP TEST:")
print("-" * 40)
for form in form_levels:
    try:
        # Try accessing streams through reverse relationship
        streams_via_reverse = form.streams.all()
        print(f"Form {form.number}: {streams_via_reverse.count()} streams (via reverse)")
    except Exception as e:
        print(f"Form {form.number}: ERROR - {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)