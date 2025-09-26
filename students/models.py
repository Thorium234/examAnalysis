from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from school.models import School
from utils.validators import kenyan_phone_number_validator, format_kenyan_phone_number

# We will need to link students to the School model. This is key for multi-tenancy.
class Student(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students')
    name = models.CharField(max_length=255)
    admission_number = models.CharField(max_length=50)
    kcpe_marks = models.IntegerField(null=True, blank=True)
    stream = models.CharField(max_length=50)
    form_level = models.IntegerField(choices=[(1, 'Form 1'), (2, 'Form 2'), (3, 'Form 3'), (4, 'Form 4')])
    
    # We will format this phone number automatically when saved.
    phone_contact = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[kenyan_phone_number_validator]
    )

    # A many-to-many relationship with subjects to handle optional subjects.
    # We use a string reference 'subjects.Subject' to avoid a circular import.
    subjects = models.ManyToManyField('subjects.Subject', related_name='students', blank=True)

    def save(self, *args, **kwargs):
        # Auto-format the phone number to the international Kenyan format
        self.phone_contact = format_kenyan_phone_number(self.phone_contact)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.admission_number})"

    class Meta:
        unique_together = ('school', 'admission_number')

# A model to manage the automatic advancement of students to the next class.
class StudentAdvancement(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='advancements')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='advancements')
    from_form_level = models.IntegerField()
    to_form_level = models.IntegerField()
    advancement_year = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} moved from Form {self.from_form_level} to Form {self.to_form_level} in {self.advancement_year}"
