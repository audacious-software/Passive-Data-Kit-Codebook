import markdown

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def codebook_markdown(value):
    return mark_safe(markdown.markdown(value)) # nosec
