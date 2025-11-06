from django import template

register = template.Library()

@register.filter(name='position_icon')
def position_icon(position_string):

    position_string = position_string.lower()
    if 'punong barangay' in position_string:
        return "bi bi-person-badge-fill"
    elif 'kagawad' in position_string:
        return "bi bi-person-check-fill"
    elif 'sk chair' in position_string:
        return "bi bi-person-heart"
    elif 'secretary' in position_string:
        return "bi bi-pencil-square"
    elif 'treasurer' in position_string:
        return "bi bi-cash-coin"
    elif 'chief tanod' in position_string:
        return "bi bi-shield-fill"
    elif 'lupong tagapamayapa' in position_string:
        return "bi bi-people-fill"
    elif 'barangay tanod' in position_string:
        return "bi bi-shield-shaded"
    else:
        return "bi bi-person-fill"
    
@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Checks if a user is a member of a group.
    Usage: {% if request.user|has_group:"Group Name" %}
    """
    if user.is_authenticated:
        return user.groups.filter(name=group_name).exists()
    return False

@register.filter(name='get')
def get(dictionary, key):
    return dictionary.get(key)

@register.filter(name='social_icon')
def social_icon(url_string):
    if not url_string:
        return "bi bi-link-45deg" 

    url_lower = url_string.lower()

    if 'facebook.com' in url_lower:
        return "bi bi-facebook"
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return "bi bi-twitter-x"
    elif 'instagram.com' in url_lower:
        return "bi bi-instagram"
    elif 'linkedin.com' in url_lower:
        return "bi bi-linkedin"
    elif 'tiktok.com' in url_lower:
        return "bi bi-tiktok"
    elif 'youtube.com' in url_lower:
        return "bi bi-youtube"
    elif 'google.com' in url_lower or 'gmail.com' in url_lower:
        return "bi bi-google"
    
    return "bi bi-link-45deg"