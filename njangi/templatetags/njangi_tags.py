from django import template
from njangi.models import LEVEL_CONTRIBUTIONS
from django.contrib.auth import get_user_model

register = template.Library()


@register.simple_tag
def level_contribution(level):
    try:
        return LEVEL_CONTRIBUTIONS[level]
    except KeyError:
        return 0


@register.simple_tag(name='upgrade_to')
def upgrade_to(user_id):
    try:
        user = get_user_model().objects.get(pk=user_id)
        level = user.level
        if level < 6:
            new_level = level + 1
        elif level == 6:
            new_level = 6
        else:
            new_level = 0
        return new_level
    except get_user_model().DoesNotExist():
        return 0


@register.simple_tag(name='replace_underscore')
def replace_underscore(value):
    return value.replace('_', ' ')


@register.simple_tag(name='r_strip')
def r_strip(amount):
    return ("%f" % amount).rstrip('0').rstrip('.')