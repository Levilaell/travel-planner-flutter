# itineraries/templatetags/filters.py
import re

from django import template

register = template.Library()

@register.filter
def strip_markdown(value):
    """
    Remove marcações básicas de markdown: ###, **, ---, etc.
    """
    value = re.sub(r'^#{1,6}\s*', '', value, flags=re.MULTILINE)  # títulos ###
    value = re.sub(r'\*\*(.*?)\*\*', r'\1', value)                # **negrito**
    value = re.sub(r'\*(.*?)\*', r'\1', value)                    # *itálico*
    value = re.sub(r'^---$', '', value, flags=re.MULTILINE)      # ---
    value = re.sub(r'`(.*?)`', r'\1', value)                      # `code`
    # remove emojis (básico)
    value = re.sub(r'[^\w\s,.\-;:()\[\]\/]', '', value)

    return value.strip()
