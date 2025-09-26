# Location: school_cheng_ji/accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver 
from utils.validators import format_kenyan_phone_number, kenyan_phone_number_validator

# A custom User model to allow for school multi-tenancy.
# We inherit from Django's AbstractUser to keep built-in functionality.
class CustomUser(AbstractUser):
    # Link a user to a specific school. This is the core of our multi-tenancy.
    school = models.ForeignKey(
        'school.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # We will use the username field for a user's email address
    # For a teacher, we can set it to their email. For a student, we can make it a combination of their admission number and school code.

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    roles = models.ManyToManyField(Role, related_name='profiles')
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[kenyan_phone_number_validator]
    )
    
    def save(self, *args, **kwargs):
        # Auto-format the phone number to the international Kenyan format
        self.phone_number = format_kenyan_phone_number(self.phone_number)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

class TeacherClass(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='teacher_classes')
    school = models.ForeignKey(
        'school.School',
        on_delete=models.CASCADE,
        related_name='teacher_classes'
    )

    FORM_LEVEL_CHOICES = [
        (1, 'Form 1'),
        (2, 'Form 2'),
        (3, 'Form 3'),
        (4, 'Form 4')
    ]
    
    form_level = models.IntegerField(choices=FORM_LEVEL_CHOICES)
    stream = models.CharField(max_length=20)
    is_class_teacher = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('teacher', 'school', 'form_level', 'stream')
    
    def __str__(self):
        teacher_name = self.teacher.get_full_name() or self.teacher.username
        return f"{teacher_name} - Form {self.form_level} {self.stream}"
    
    @property
    def class_name(self):
        return f"Form {self.form_level} {self.stream}"

class TeacherSubject(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='taught_subjects')
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    
    class Meta:
        unique_together = ('teacher', 'subject')
        
    def __str__(self):
        return f"{self.teacher.get_full_name() or self.teacher.username} teaches {self.subject.name}"
