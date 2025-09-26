# exams/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Returns the value from a dictionary given a key.
    """
    return dictionary.get(key)
