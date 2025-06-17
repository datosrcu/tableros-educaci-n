from django import template
register = template.Library()

@register.filter
def to_int(start, end):
    return range(start, end+1)
