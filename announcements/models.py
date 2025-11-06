from django.db import models
from django.conf import settings

class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField() # Dito ise-save ang HTML from Quill.js
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    featured_image = models.ImageField(upload_to='announcement_images/', blank=True, null=True)
    date_published = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True) # Para pwede i-draft

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date_published']