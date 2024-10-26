from django import template

register = template.Library()

@register.filter
def dict_key(value, arg):
    """Gets a value from a dictionary given a key"""
    try:
        return value[arg]
    except KeyError:
        return None