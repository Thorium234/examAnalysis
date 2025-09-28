from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from students.models import Student
from school.models import School

User = get_user_model()

class StudentBackend(BaseBackend):
    """
    Custom authentication backend for students using school_code + admission_number
    """

    def authenticate(self, request, school_code=None, admission_number=None, **kwargs):
        if school_code and admission_number:
            try:
                # Find the school by code
                school = School.objects.get(school_code=school_code.upper())

                # Find the student by admission number in that school
                student = Student.objects.get(
                    school=school,
                    admission_number=admission_number.upper()
                )

                # Check if a user account exists for this student
                # We'll use a combination of school_code and admission_number as username
                username = f"{school_code.lower()}_{admission_number.lower()}"

                try:
                    user = User.objects.get(username=username)
                    return user
                except User.DoesNotExist:
                    # Create a user account for the student if it doesn't exist
                    user = User.objects.create_user(
                        username=username,
                        first_name=student.name.split()[0] if student.name else '',
                        last_name=' '.join(student.name.split()[1:]) if student.name and len(student.name.split()) > 1 else '',
                        is_staff=False,
                        is_superuser=False
                    )
                    user.school = school
                    user.save()

                    # Create a profile for the student
                    from .models import Profile, Role
                    student_role, created = Role.objects.get_or_create(name='Student')
                    Profile.objects.create(user=user)
                    user.profile.roles.add(student_role)

                    return user

            except (School.DoesNotExist, Student.DoesNotExist):
                return None

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None