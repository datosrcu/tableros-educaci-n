from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter(name='is_select')
def is_select(field):
    from django.forms.widgets import Select
    return isinstance(field.field.widget, Select)
