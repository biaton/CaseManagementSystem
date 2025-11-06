from django import forms
from django.contrib.auth.forms import UserCreationForm, password_validation
from django.core.exceptions import ValidationError
from users.models import CustomUser
from cases.choices import ACTIONABLE_STATUS_CHOICES, REPORT_STATUS_CHOICES
from cases.models import Schedule

class OfficialSignUpForm(UserCreationForm):
    
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'middle_name', 'suffix',
            'gender', 'phone_number', 'barangay_position', 'email'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Loop sa lahat ng fields na nasa Meta para sa styling
        for field_name in self.Meta.fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'form-input mt-1'})

        # Special styling para sa dropdowns
        self.fields['gender'] = forms.ChoiceField(
            choices=[('', 'Select Gender...'), ('Male', 'Male'), ('Female', 'Female')],
            required=False,
            widget=forms.Select(attrs={'class': 'form-input form-select mt-1'})
        )
        self.fields['barangay_position'].widget.attrs.update({
            'class': 'form-input form-select mt-1'
        })
        self.fields['barangay_position'].choices = [('', 'Select Position...')] + self.fields['barangay_position'].choices[1:]

        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({'class': 'form-input mt-1', 'placeholder': 'Enter password'})
            self.fields['password1'].required = False
            self.fields['password1'].help_text = "Leave blank to auto-generate a password."

        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({'class': 'form-input mt-1', 'placeholder': 'Enter password again'})
            self.fields['password2'].required = False


    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
        return user
    
class UpdateCaseStatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Update Status To", # Nagdagdag ako ng label para mas malinis
        choices=ACTIONABLE_STATUS_CHOICES, # Gagamitin na natin ang bago at mas maikling listahan
        widget=forms.Select(attrs={'class': 'w-full py-2 px-3 border rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'})
    )
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'w-full py-2 px-3 border rounded-lg', 'placeholder': 'Add remarks or details about this action...'}),
        required=False
    )

class ScheduleForm(forms.ModelForm):
    # I-override natin ang proceeding_type para maging dropdown
    schedule_type = forms.ChoiceField(
        choices=[('Summon', 'Summon'), ('Mediation', 'Mediation'), ('Conciliation', 'Conciliation')],
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}), required=False)

    class Meta:
        model = Schedule
        fields = ['schedule_type', 'appearance_date', 'appearance_time', 'remarks']
        widgets = {
            'appearance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'appearance_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
        }

class AmicableSettlementForm(forms.Form):
    amicable_settlement_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )
    agreement_details = forms.CharField(
        label="Details of Agreement / Pinagkasunduan",
        widget=forms.Textarea(attrs={'rows': 10, 'class': 'form-input', 'placeholder': 'Ilahad dito ang buong detalye ng kasunduan ng dalawang panig...'})
    )

class UpdateReportStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=REPORT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full py-2 px-3 border rounded-lg'})
    )
    action_taken = forms.CharField(
        label="Action Taken / Remarks",
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'w-full py-2 px-3 border rounded-lg', 'placeholder': 'Describe the action taken by the barangay...'}),
        required=True # Kailangan ito para ma-document
    )
class QuickUpdateReportStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=REPORT_STATUS_CHOICES, # Gagamitin natin ang kumpletong list
        widget=forms.Select(attrs={'class': 'w-full py-2 px-3 border rounded-lg'})
    )

class OfficialUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'middle_name', 'suffix',
            'gender', 'phone_number', 'barangay_position', 'email'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input mt-1'})
        
        self.fields['gender'].widget.attrs.update({'class': 'form-input form-select mt-1'})
        self.fields['barangay_position'].widget.attrs.update({'class': 'form-input form-select mt-1'})

class OfficialProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # Ito lang ang fields na pwedeng palitan
        fields = ['address', 'phone_number', 'email', 'birthday']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.DateInput):
                field.widget.attrs['type'] = 'date'
            field.widget.attrs.update({'class': 'form-input mt-1'})
        
        if 'birthday' in self.fields:
            self.fields['birthday'].widget = forms.DateInput(
                attrs={
                    'type': 'date', 
                    'class': 'form-input mt-1'
                }
            )

class OfficialPasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Your Official Email Address", widget=forms.EmailInput(attrs={'class': 'form-input'}))

class OfficialVerifyOTPForm(forms.Form):
    otp = forms.CharField(label="6-Digit OTP", max_length=6, widget=forms.TextInput(attrs={'class': 'form-input text-center tracking-[1em]'}))

class OfficialSetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    new_password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("new_password1") != cleaned_data.get("new_password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
    
