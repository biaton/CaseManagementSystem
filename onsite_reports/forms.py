from django import forms
from cases.choices import INCIDENT_TYPE_CHOICES

class OnSiteBlotterForm(forms.Form):
    # Complainant Details (I-type lahat)
    complainant_first_name = forms.CharField(label="Complainant's First Name", max_length=100)
    complainant_last_name = forms.CharField(label="Complainant's Last Name", max_length=100)
    complainant_middle_name = forms.CharField(label="Complainant's Middle Name", required=False)
    complainant_suffix = forms.CharField(label="Complainant's Suffix", required=False)
    complainant_contact_number = forms.CharField(label="Complainant's Contact No.", max_length=20)
    complainant_address = forms.CharField(label="Complainant's Address", widget=forms.Textarea(attrs={'rows': 3}))

    # Respondent Details
    respondent_first_name = forms.CharField(max_length=100)
    respondent_last_name = forms.CharField(max_length=100)
    respondent_middle_name = forms.CharField(required=False)
    respondent_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    
    # Incident Details
    incident_type = forms.ChoiceField(choices=INCIDENT_TYPE_CHOICES)
    date_of_incident = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    location_of_incident = forms.CharField(max_length=255)
    incident_description = forms.CharField(label="Narrative / Incident Description", widget=forms.Textarea(attrs={'rows': 5}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input mt-1'})

class OnSiteReportForm(forms.Form):
    # Informant Details
    informant_first_name = forms.CharField(label="Informant's First Name", max_length=100)
    informant_last_name = forms.CharField(label="Informant's Last Name", max_length=100)
    informant_contact_number = forms.CharField(label="Informant's Contact No.", max_length=20)
    
    # Report Details
    date_of_incident = forms.DateField(label="Date of Observation/Incident", widget=forms.DateInput(attrs={'type': 'date'}))
    location_of_incident = forms.CharField(label="Location of Observation/Incident", max_length=255)
    report_details = forms.CharField(label="Details of the Report", widget=forms.Textarea(attrs={'rows': 6}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input mt-1'})