from django import template
register = template.Library()


@register.filter(name='addcss')
def addcss(field, css):

    attrs = {}
    definition = css.split(',')
    class_old = field.field.widget.attrs.get('class', None)

    for d in definition:
        if ':' not in d:
            attrs['class'] = d
        else:
            t, v = d.split(':')
            attrs[t] = v
    class_added = attrs.get('class', None)
    class_new = class_old + ' ' + class_added if class_old else class_added
    attrs['class'] = class_new if class_new else None
    return field.as_widget(attrs=attrs)
