# school/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Returns the value from a dictionary given a key.
    """
    return dictionary.get(key)

@register.filter(name='is_teacher')
def is_teacher(user):
    """
    Returns True if the user has a 'Teacher' role, False otherwise.
    """
    if hasattr(user, 'profile') and user.profile:
        return user.profile.roles.filter(name='Teacher').exists()
    return False