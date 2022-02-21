from django import template

register = template.Library() 

@register.filter
def has_group(user, name):
    return user.groups.filter(name=name).exists() 
