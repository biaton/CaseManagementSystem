# system_settings/forms.py
from django import forms
from .models import BarangayInfo, Hotline, ExternalLink, OfficialDisplay, Contact, LuponMember

class BarangayInfoForm(forms.ModelForm):
    class Meta:
        model = BarangayInfo
        fields = ['name', 'city', 'province', 'logo']

class HotlineForm(forms.ModelForm):
    class Meta:
        model = Hotline
        fields = ['name', 'number', 'order']

class ExternalLinkForm(forms.ModelForm):
    class Meta:
        model = ExternalLink
        fields = ['name', 'url', 'icon_class']

class OfficialDisplayForm(forms.ModelForm):
    class Meta:
        model = OfficialDisplay
        fields = ['full_name', 'position', 'order', 'profile_picture', 'social_media_link']

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'number', 'email', 'address']

class LuponMemberAddForm(forms.ModelForm):
    class Meta:
        model = LuponMember
        fields = ['full_name', 'position']

# Ito ay para sa pag-update
class LuponMemberUpdateForm(forms.ModelForm):
    class Meta:
        model = LuponMember
        fields = ['full_name', 'position', 'is_active']