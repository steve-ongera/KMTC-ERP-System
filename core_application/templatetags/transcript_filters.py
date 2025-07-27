# templatetags/transcript_filters.py
from django import template

register = template.Library()

@register.filter
def dict_key(dictionary, key):
    """
    Access dictionary value by key in templates
    Usage: {{ dict|dict_key:"key_name" }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None



@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key
    Usage: {{ dict|get_item:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, {})
    return {}

@register.filter
def get_nested(dictionary, keys):
    """
    Get nested value from dictionary using dot notation
    Usage: {{ grades_data|get_nested:"14.theory_marks" }}
    """
    if not isinstance(dictionary, dict):
        return None
    
    try:
        key_parts = str(keys).split('.')
        result = dictionary
        for key in key_parts:
            if isinstance(result, dict):
                # Try integer key first, then string key
                try:
                    int_key = int(key)
                    result = result.get(int_key, result.get(key, None))
                except ValueError:
                    result = result.get(key, None)
            else:
                return None
            
            if result is None:
                return None
        return result
    except:
        return None

@register.filter
def add(value, arg):
    """
    Add the arg to the value
    Usage: {{ value|add:"text" }}
    """
    try:
        return str(value) + str(arg)
    except:
        return value

@register.filter
def get_attr(obj, attr_name):
    """
    Get attribute from object
    Usage: {{ obj|get_attr:"attribute_name" }}
    """
    try:
        return getattr(obj, attr_name, None)
    except:
        return None