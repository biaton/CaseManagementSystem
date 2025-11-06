# reports_analytics/templatetags/report_extras.py
from django import template
register = template.Library()

@register.filter(name='get')
def get(dictionary, key):
    return dictionary.get(key)