from django import template
register = template.Library()

@register.filter
def to_int(start, end):
    return range(start, end+1)

@register.filter(name='separador_miles')
def separador_miles(val):
    if val is None or val == '':
        return '0'
    try:
        clean_str = str(val).replace('$', '').strip()
        num = int(round(float(clean_str)))
        return f"{num:,}".replace(',', '.')
    except (ValueError, TypeError):
        return str(val)
