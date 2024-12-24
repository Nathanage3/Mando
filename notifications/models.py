from django.db import models
from django.conf import settings

class Notification(models.Model):
    MESSAGE = 'message'
    ALERT = 'alert'
    PROMOTION = 'promotion'
    
    NOTIFICATION_TYPES = [
        (MESSAGE, 'Message'),
        (ALERT, 'Alert'),
        (PROMOTION, 'Promotion'),
    ]
   
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100, blank=True, null=True)
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default=MESSAGE)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return f'{self.get_notification_type_display()} for {self.user.username}'
    
    def is_expired(self):
        from django.utils import timezone
        return self.expires_at and self.expires_at < timezone.now()