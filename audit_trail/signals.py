# audit_trail/signals.py
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.handlers.wsgi import WSGIRequest

from .models import AuditLog
from cases.models import Blotter
from users.models import CustomUser

# Global variable to hold the current request
_thread_locals = {"request": None}

def get_current_request():
    return _thread_locals.get("request")

# Middleware to capture the request
class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals["request"] = request
        response = self.get_response(request)
        _thread_locals.pop("request", None)
        return response

def get_client_ip(request):
    if not request: return "N/A"
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# --- USER ACTIONS ---

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    if user.is_staff:
        AuditLog.objects.create(user=user, action="LOGGED IN", details=f"Logged in from IP: {get_client_ip(request)}")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user and user.is_staff:
        AuditLog.objects.create(user=user, action="LOGGED OUT", details=f"Logged out.")
        
@receiver(post_save, sender=CustomUser)
def log_user_save(sender, instance, created, **kwargs):
    request = get_current_request()
    actor = request.user if request and request.user.is_authenticated else None

    if created and instance.is_staff:
        action = "CREATED OFFICIAL"
        details = f"Official account '{instance.email}' was created by {actor.email if actor else 'System'}."
        AuditLog.objects.create(user=actor, action=action, details=details)
    elif not created and instance.is_staff:
        # We can add more logic here to track what was changed
        action = "UPDATED OFFICIAL"
        details = f"Official account '{instance.email}' was updated by {actor.email if actor else 'System'}."
        AuditLog.objects.create(user=actor, action=action, details=details)


# --- BLOTTER CASE ACTIONS ---

@receiver(post_save, sender=Blotter)
def log_blotter_save(sender, instance, created, **kwargs):
    request = get_current_request()
    actor = request.user if request and request.user.is_authenticated else None
    
    if created:
        action = "CREATED BLOTTER"
        details = f"Blotter case '{instance.blotter_id}' was created by {actor.get_full_name() if actor else 'System'}."
        AuditLog.objects.create(user=actor, action=action, details=details)
    else:
        action = "UPDATED BLOTTER"
        details = f"Blotter case '{instance.blotter_id}' was updated. Status is now '{instance.get_status_display()}'."
        AuditLog.objects.create(user=actor, action=action, details=details)

@receiver(post_delete, sender=Blotter)
def log_blotter_delete(sender, instance, **kwargs):
    request = get_current_request()
    actor = request.user if request and request.user.is_authenticated else None

    action = "DELETED BLOTTER"
    details = f"Blotter case '{instance.blotter_id}' (Complainant: {instance.complainant.get_full_name()}) was deleted by {actor.get_full_name() if actor else 'System'}."
    AuditLog.objects.create(user=actor, action=action, details=details)