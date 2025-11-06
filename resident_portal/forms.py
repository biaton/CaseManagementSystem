# resident_portal/forms.py
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from users.models import CustomUser
from cases.models import Blotter, Report
from django.contrib.auth.forms import PasswordChangeForm
from django.forms import DateInput, Textarea, ClearableFileInput
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email',) # Only include email if it's the USERNAME_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username'] # Remove username if it's not used

# =======================================================================
# FORM PARA SA RESIDENT LOGIN PAGE
# =======================================================================
class ResidentLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-input', 'placeholder': 'Enter your email address'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'form-input', 'placeholder': 'Enter your password'}
        )

# =======================================================================
# FORM PARA SA RESIDENT SIGN UP PAGE
# =======================================================================
class ResidentSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="Firstname / Pangalan")
    last_name = forms.CharField(max_length=150, required=True, label="Lastname / Apelyedo")
    middle_name = forms.CharField(max_length=150, required=False, label="Middlename / Gitnang Pangalan")
    suffix = forms.CharField(max_length=10, required=False, label="Suffix (Ex. Sr. / Jr. / II)")
    gender = forms.ChoiceField(
        label="Gender / Kasarian",
        choices=[('', 'Select  '), ('Male', 'Male / Lalaki'), ('Female', 'Female / Babae')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    birthday = forms.DateField(
        label="Birthday / Kaarawan",
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    address = forms.CharField(
        label="Address / Tirahan",
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2,})
    )
    phone_number = forms.CharField(max_length=11, required=True, label="Phone Number / Numero ng telepono")
    
    email = forms.EmailField(required=True, label="Email Address")

    terms = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must agree to the terms and conditions.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    id_image = forms.ImageField(
        label="Valid ID Photo",
        required=True,
        widget=forms.ClearableFileInput(attrs={ # Direct config here
            'class': 'd-none',
            'id': 'id_id_image', # Use 'id_id_image' as per Django's default for 'id_image' field
        })
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'middle_name', 'suffix',
            'gender', 'address', 'birthday', 'phone_number', 'email',
            'id_image', 'terms'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Apply Bootstrap classes to most fields in a single loop
        for field_name, field in self.fields.items():
            # Exclude password fields and special widgets from generic form-control styling
            if field_name not in ['password1', 'password2', 'terms', 'id_image', 'gender', 'birthday', 'address']:
                field.widget.attrs.update({'class': 'form-control form-control-sm'})
            
            # Specific styling for password fields (inherited from UserCreationForm)
            if field_name == 'password1':
                field.widget.attrs.update({
                    'class': 'form-control form-control-sm',
                    'placeholder': 'Enter your password',
                    'minlength': 8 # Example: enforce minimum length
                })
            
            if field_name == 'password2':
                field.widget.attrs.update({
                    'class': 'form-control form-control-sm',
                    'placeholder': 'Confirm your password',
                    'minlength': 8 # Example: enforce minimum length
                })
            
            # Add placeholders for other text fields if desired
            if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.EmailInput):
                if not field.widget.attrs.get('placeholder'): # Only if no placeholder is already set
                    field.widget.attrs['placeholder'] = f"Enter your {field_name.replace('_', ' ')}"
        
        if 'username' in self.fields:
             del self.fields['username'] # Example: if your CustomUser is email-based only
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Tanggalin ang `user.is_active = True` dito kung ang views.py ang magse-set nito to False
        # user.is_active = True # Ito ang magko-conflict sa views.py
        if commit:
            user.save()
        return user
    
# =======================================================================
# FORM PARA SA PAGBABAGO NG PASSWORD NG RESIDENT
# =======================================================================
class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Your Email Address", widget=forms.EmailInput(attrs={'class': 'form-control'}))

class VerifyOTPForm(forms.Form):
    #otp = forms.CharField(label="6-Digit OTP", max_length=6, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '______'}))
    otp = forms.CharField(
        widget=forms.HiddenInput(), 
        max_length=6
    )

class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("The two password fields didn't match.")
        return cleaned_data

# =======================================================================
# FORM PARA SA PAGPAPALIT NG CREATE BLOTTER FORM
# =======================================================================
class BlotterForm(forms.ModelForm):
    class Meta:
        model = Blotter
        fields = [
            'complainant_first_name', 'complainant_last_name', 'complainant_middle_name',
            'complainant_address', 'complainant_suffix', 'complainant_contact_number',
            'date_of_incident', 'location_of_incident', 'incident_description', 
            'incident_image', 'respondent_last_name', 'respondent_first_name',
            'respondent_middle_name', 'respondent_address',
            'latitude', 'longitude', 'complainant_suffix', 'complainant_contact_number', 'incident_type',
        ]
        widgets = {
            'complainant_first_name': forms.TextInput(attrs={'placeholder': 'First name / Pangalan', 'class': 'form-input-style'}),
            'complainant_last_name': forms.TextInput(attrs={'placeholder': 'Last name / Apelyido', 'class': 'form-input-style'}),
            'complainant_middle_name': forms.TextInput(attrs={'placeholder': 'Middle name / Gitnang Pangalan', 'class': 'form-input-style'}),
            'complainant_address': forms.TextInput(attrs={'placeholder': 'Address / Tirahan', 'class': 'form-input-style'}),
            'complainant_suffix': forms.TextInput(attrs={'placeholder': 'e.g., Jr., Sr., III', 'class': 'form-input-style'}),
            'complainant_contact_number': forms.TextInput(attrs={'placeholder': 'e.g., 09123456789', 'class': 'form-input-style'}),
            'date_of_incident': forms.DateInput(attrs={'type': 'date', 'class': 'form-input-style'}),
            'incident_description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Isalaysay ang buong pangyayari...', 'class': 'form-input-style'}),
            'respondent_last_name': forms.TextInput(attrs={'placeholder': 'Apelyido', 'class': 'form-input-style'}),
            'respondent_first_name': forms.TextInput(attrs={'placeholder': 'Pangalan', 'class': 'form-input-style'}),
            'respondent_middle_name': forms.TextInput(attrs={'placeholder': 'Gitnang Pangalan', 'class': 'form-input-style'}),
            'respondent_address': forms.TextInput(attrs={'placeholder': 'Kumpletong Tirahan', 'class': 'form-input-style'}),
            'incident_image': forms.ClearableFileInput(attrs={'class': 'form-input-style'}),
            'latitude': forms.HiddenInput(), 
            'longitude': forms.HiddenInput(),
            'incident_type': forms.Select(attrs={'class': 'form-input-style'}),
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = [
            'complainant_first_name', 'complainant_last_name', 'complainant_middle_name',
            'complainant_address', 'complainant_suffix', 'complainant_contact_number',
            'informant_contact_number', 'date_of_incident',
            'location_of_incident', 'report_details',
            'latitude', 'longitude'
        ]
        widgets = {
            'complainant_first_name': forms.TextInput(attrs={'placeholder': 'First name / Pangalan', 'class': 'form-input-style'}),
            'complainant_last_name': forms.TextInput(attrs={'placeholder': 'Last name / Apelyido', 'class': 'form-input-style'}),
            'complainant_middle_name': forms.TextInput(attrs={'placeholder': 'Middle name / Gitnang Pangalan', 'class': 'form-input-style'}),
            'complainant_address': forms.TextInput(attrs={'placeholder': 'Address / Tirahan', 'class': 'form-input-style'}),
            'complainant_suffix': forms.TextInput(attrs={'placeholder': 'e.g., Jr., Sr., III', 'class': 'form-input-style'}),
            'complainant_contact_number': forms.TextInput(attrs={'placeholder': 'e.g., 09123456789', 'class': 'form-input-style'}),
            'informant_contact_number': forms.TextInput(attrs={'placeholder': 'e.g., 09123456789', 'class': 'form-input-style'}),
            'date_of_incident': forms.DateInput(attrs={'type': 'date', 'class': 'form-input-style'}),
            'report_details': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Isalaysay ang iyong ulat o concern...', 'class': 'form-input-style'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

class ResidentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # Ito lang ang fields na pwedeng i-update ng user
        fields = [
            'first_name', 'last_name', 'middle_name', 'suffix',
            'gender', 'birthday', 'address', 'phone_number'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply styling sa lahat ng fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.DateInput):
                field.widget.attrs['type'] = 'date'
            field.widget.attrs.update({'class': 'form-input mt-1'})