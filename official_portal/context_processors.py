from system_settings.models import OfficialDisplay 
from audit_trail.models import OfficialNotification

def official_list(request):
    # Kunin ang listahan mula sa bago nating model
    officials = OfficialDisplay.objects.all()
    return {'sidebar_officials': officials} 

def official_notifications(request):
    if request.user.is_authenticated and request.user.is_staff:
        notifications = OfficialNotification.objects.filter(is_read=False)
        return {
            'official_notifications': notifications,
            'official_unread_count': notifications.count()
        }
    return {}   