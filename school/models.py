from django.db import models
from django.core.validators import EmailValidator
from utils.validators import format_kenyan_phone_number, kenyan_phone_number_validator

# This is the central model for our multi-tenant architecture.
class School(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[kenyan_phone_number_validator]
    )
    email = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        validators=[EmailValidator()]
    )
    
    def save(self, *args, **kwargs):
        # Auto-format the phone number to the international Kenyan format
        self.phone_number = format_kenyan_phone_number(self.phone_number)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
