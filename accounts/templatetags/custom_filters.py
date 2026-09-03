from django import template

register = template.Library()


@register.filter(name='replace_underscores')
def replace_underscores(value):
    """
    Turns 'view_invoice' into 'view invoice' for display purposes.
    Used on permission codenames in role_permissions.html.
    """
    if value is None:
        return value
    return str(value).replace('_', ' ')