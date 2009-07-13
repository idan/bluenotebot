from django.utils.safestring import mark_safe
from django import template
import re

register = template.Library()

@register.filter
def highlight(text, terms):
    for term in terms:
        patt = re.compile('(?P<term>{0})'.format(term), re.I)
        text = patt.sub('<span class="highlight">\g<term></span>', text)
    return mark_safe(text)

highlight.is_safe = True