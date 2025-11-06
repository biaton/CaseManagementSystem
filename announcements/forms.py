from django import forms
from .models import Announcement

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'featured_image', 'is_published']
        widgets = {
            'content': forms.HiddenInput(), # Itatago natin 'to, si Quill.js ang maglalagay ng value
        }