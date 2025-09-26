# Location: school_cheng_ji/utils/validators.py

import re
from django.core.validators import RegexValidator

def format_kenyan_phone_number(phone_number):
    """
    Formats a Kenyan phone number to the international E.164 format.
    Accepts formats like '07XXXXXXXX' or '+2547XXXXXXXX'.
    """
    if not phone_number:
        return None
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone_number)
    
    # Check if the number starts with '07'
    if digits.startswith('07') and len(digits) == 10:
        return f'+254{digits[1:]}'
    # Check if the number starts with '254'
    elif digits.startswith('254') and len(digits) == 12:
        return f'+{digits}'
    # Check if the number starts with '7'
    elif digits.startswith('7') and len(digits) == 9:
        return f'+254{digits}'
    
    return phone_number

# Reusable phone number validator
kenyan_phone_number_validator = RegexValidator(
    regex=r'^\+?254\d{9}$',
    message="Phone number must be entered in the international format: '+2547XXXXXXXX'."
)
