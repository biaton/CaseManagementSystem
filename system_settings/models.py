from django.db import models
from django.conf import settings

class BarangayInfo(models.Model):
    name = models.CharField(max_length=100, default="Barangay Addition Hills")
    city = models.CharField(max_length=100, default="City of Mandaluyong")
    province = models.CharField(max_length=100, default="Metro Manila")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    # Pwede kang magdagdag ng iba pang info dito

    def __str__(self):
        return self.name

class Hotline(models.Model):
    name = models.CharField(max_length=100) # e.g., "Police", "Fire Department"
    number = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0) # Para sa sorting

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} - {self.number}"

class ExternalLink(models.Model):
    name = models.CharField(max_length=100) # e.g., "Facebook Page", "Official Website"
    url = models.URLField()
    icon_class = models.CharField(max_length=50, blank=True, help_text="e.g., 'bi bi-facebook'")

    def __str__(self):
        return self.name
    
class OfficialDisplay(models.Model):
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0, help_text="Set order of display, 0 is highest.")

    profile_picture = models.ImageField(
        upload_to='official_profiles/', 
        blank=True, 
        null=True
    )
    social_media_link = models.URLField(
        max_length=255, 
        blank=True, 
        help_text="Optional: Link to Facebook, LinkedIn, etc."
    )

    class Meta:
        ordering = ['order', 'full_name']

    def __str__(self):
        return f"{self.full_name} - {self.position}"
    
class Contact(models.Model):
    name = models.CharField(max_length=100) # e.g., "City Hall", "DSWD Office"
    number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.name
    
class LuponSchedule(models.Model):
    lupon_member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    day_of_week = models.IntegerField(choices=[(0, 'Monday'),(1, 'Tuesday'),(2, 'Wednesday'),(3, 'Thursday'),(4, 'Friday')])
    is_available = models.BooleanField(default=False)

    class Meta:
        unique_together = ('lupon_member', 'day_of_week') # Para isang entry lang per lupon per araw

    def __str__(self):
        return f"{self.lupon_member.get_full_name()} - {self.get_day_of_week_display()}"
    
class LuponMember(models.Model):
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=100, default="Lupong Tagapamayapa")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

class LuponAvailability(models.Model):
    lupon_member = models.ForeignKey(LuponMember, on_delete=models.CASCADE, related_name='availabilities')
    # Monday=0, Tuesday=1, ..., Friday=4
    day_of_week = models.IntegerField(choices=[(i, i) for i in range(5)]) 
    is_available = models.BooleanField(default=False)

    class Meta:
        unique_together = ('lupon_member', 'day_of_week')