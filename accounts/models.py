from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_ROLES = (
        ('super_user', 'Super User'),
        ('principal', 'Principal'),
        ('deputy', 'Deputy Principal'),
        ('dos', 'Director of Studies'),
        ('teacher', 'Teacher'),
    )
    
    role = models.CharField(max_length=20, choices=USER_ROLES, default='teacher')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    def __str__(self):
        full_name = self.get_full_name() or self.username
        return f"{full_name} ({dict(self.USER_ROLES).get(self.role, self.role)})"
    
    @property
    def is_admin_user(self):
        return self.role in ['super_user', 'principal', 'deputy', 'dos']
    
    @property
    def can_manage_students(self):
        return self.role in ['super_user', 'principal', 'deputy', 'dos']
    
    @property
    def can_view_all_results(self):
        return self.role in ['super_user', 'principal', 'deputy', 'dos']

class TeacherSubject(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_subjects')
    subject_name = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('teacher', 'subject_name')
    
    def __str__(self):
        teacher_name = self.teacher.get_full_name() or self.teacher.username
        return f"{teacher_name} - {self.subject_name}"

class TeacherClass(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_classes')
    form_level = models.IntegerField(choices=[(1, 'Form 1'), (2, 'Form 2'), (3, 'Form 3'), (4, 'Form 4')])
    stream = models.CharField(max_length=20)
    is_class_teacher = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('teacher', 'form_level', 'stream')
    
    def __str__(self):
        teacher_name = self.teacher.get_full_name() or self.teacher.username
        return f"{teacher_name} - Form {self.form_level} {self.stream}"
    
    @property
    def class_name(self):
        return f"Form {self.form_level} {self.stream}" 