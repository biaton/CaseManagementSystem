from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_email = self.user.email if self.user else "System"
        return f"{user_email} - {self.action} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-timestamp']

class OfficialNotification(models.Model):
    # Kanino ipapakita ang notif? Pwede nating i-broadcast sa lahat.
    # For simplicity, hindi natin ilalagay kung sino ang recipient.
    message = models.TextField()
    link = models.URLField(blank=True, null=True) # Link papunta sa action
    is_read = models.BooleanField(default=False) # Para sa future "mark as read"
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return self.message[:50]