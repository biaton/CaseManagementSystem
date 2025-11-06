from django.db import models
from django.utils import timezone 
from django.conf import settings
import datetime
from .choices import CASE_STATUS_CHOICES, INCIDENT_TYPE_CHOICES, REPORT_STATUS_CHOICES
from users.models import CustomUser

class Case(models.Model):
    # -- Basic Case Information --
    case_number = models.CharField(max_length=50, unique=True, verbose_name="Case Number")
    client_name = models.CharField(max_length=100, verbose_name="Client Name")
    title = models.CharField(max_length=200, verbose_name="Case Title/Subject")
    description = models.TextField(verbose_name="Detailed Description")

    # -- Status and Tracking --
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('ON_HOLD', 'On Hold'),
        ('CLOSED', 'Closed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN',
        verbose_name="Status"
    )

    # -- Timestamps --
    date_created = models.DateTimeField(default=timezone.now, verbose_name="Date Created")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Last Updated")

    # Ito ay para maging maganda ang display niya sa admin
    def __str__(self):
        return f"{self.case_number} - {self.title}"

    class Meta:
        ordering = ['-date_created'] # Para ang pinakabago ang laging nasa taas

class Blotter(models.Model):
    # --- Case Identifier ---
    blotter_id = models.CharField(max_length=50, unique=True, editable=False, verbose_name="Blotter ID")
    
    # --- Complainant Details ---
    complainant_first_name = models.CharField(max_length=100, blank=True, verbose_name="First name / Pangalan")
    complainant_last_name = models.CharField(max_length=100, blank=True, verbose_name="Last name / Apelyido")
    complainant_middle_name = models.CharField(max_length=100, blank=True, verbose_name="Middle name / Gitnang Pangalan")
    complainant_address = models.CharField(max_length=255, blank=True, verbose_name="Address / Tirahan")
    complainant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='filed_blotters')
    # Idinagdag ang blank=True para optional
    complainant_suffix = models.CharField(max_length=10, blank=True, verbose_name="Suffix (e.g., Jr, Sr, II)")
    # Idinagdag ang blank=True para hindi mag-error kung walang laman
    complainant_contact_number = models.CharField(max_length=20, blank=True, verbose_name="Numero ng Telepono")

    # --- Incident Details ---
    date_of_incident = models.DateField(verbose_name="Petsa ng Insidente")
    location_of_incident = models.CharField(max_length=255, verbose_name="Lugar ng Insidente")
    incident_image = models.ImageField(upload_to='blotter_images/', null=True, blank=True, verbose_name="Larawan ng Insidente (Optional)")
    incident_description = models.TextField(verbose_name="Detalye ng Insidente")

    # --- Respondent Details ---
    respondent_last_name = models.CharField(max_length=100, verbose_name="Apelyido ng Respondent")
    respondent_first_name = models.CharField(max_length=100, verbose_name="Pangalan ng Respondent")
    # Idinagdag ang blank=True dahil optional ito
    respondent_middle_name = models.CharField(max_length=100, blank=True, verbose_name="Gitnang Pangalan ng Respondent")
    respondent_address = models.CharField(max_length=255, verbose_name="Tirahan ng Respondent")

    # --- Map Details ---
    # Naka-set na sa null=True, blank=True kaya okay na 'to
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # --- Timestamps and Status ---
    status = models.CharField(
        max_length=50, 
        choices=CASE_STATUS_CHOICES, 
        default='New', 
        verbose_name="Status"
    )
    incident_type = models.CharField(
        max_length=100, 
        choices=INCIDENT_TYPE_CHOICES, 
        default='Others',
        verbose_name="Uri ng Insidente"
    )
    date_filed = models.DateTimeField(auto_now_add=True)

    
    
    # ... (yung __str__ at save method ay pareho pa rin, walang pagbabago) ...
    def __str__(self):
        return self.blotter_id

    def save(self, *args, **kwargs):
        if not self.blotter_id:
            prefix = "Brgy."
            current_year = datetime.date.today().strftime('%y')
            last_entry = Blotter.objects.filter(blotter_id__startswith=f"{prefix}{current_year}").order_by('blotter_id').last()
            if last_entry:
                last_id_num = int(last_entry.blotter_id[-4:])
                new_id_num = last_id_num + 1
            else:   
                new_id_num = 1
            self.blotter_id = f"{prefix}{current_year}{new_id_num:04d}"
        super().save(*args, **kwargs)

class Report(models.Model):
    # --- Informant Details (Sino ang nag-ulat) ---
    complainant_first_name = models.CharField(max_length=100, blank=True, verbose_name="First name / Pangalan")
    complainant_last_name = models.CharField(max_length=100, blank=True, verbose_name="Last name / Apelyido")
    complainant_middle_name = models.CharField(max_length=100, blank=True, verbose_name="Middle name / Gitnang Pangalan")
    complainant_address = models.CharField(max_length=255, blank=True, verbose_name="Address / Tirahan")
    complainant_suffix = models.CharField(max_length=10, blank=True, verbose_name="Suffix (e.g., Jr, Sr, II)")
    complainant_contact_number = models.CharField(max_length=20, blank=True, verbose_name="Numero ng Telepono")
    informant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='filed_reports')
    informant_contact_number = models.CharField(max_length=20, verbose_name="Numero ng Telepono")

    # --- Incident/Report Details ---
    date_of_incident = models.DateField(verbose_name="Petsa ng Pangyayari")
    location_of_incident = models.CharField(max_length=255, verbose_name="Lugar ng Pangyayari")
    report_details = models.TextField(verbose_name="Detalye ng Ulat")

    # --- Map Details ---
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # --- Timestamps and Status ---
    status = models.CharField(
        max_length=50, 
        choices=REPORT_STATUS_CHOICES, 
        default='New', 
        verbose_name="Status"
    )
    date_filed = models.DateTimeField(auto_now_add=True)

    action_taken = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Report from {self.informant.email} on {self.date_filed.strftime('%Y-%m-%d')}"
    
class IncidentLog(models.Model):
    # I-link natin ang log sa isang specific na Blotter case
    case = models.ForeignKey(Blotter, on_delete=models.CASCADE, related_name='logs')

    # I-define natin ang mga bagong choices
    RESULT_CHOICES = [
        ('Settled', 'Settled'),
        ('Unsettled', 'Unsettled'),
    ]
    
    # Mga fields na kailangan mo
    case_title = models.CharField(max_length=255, verbose_name="Case Title")
    incident_type = models.CharField(max_length=100, verbose_name="Incident Type") # Hal. Theft, Trespassing
    status = models.CharField(max_length=50, choices=CASE_STATUS_CHOICES, verbose_name="Status")
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='processed_logs')
    date_processed = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=50, choices=RESULT_CHOICES, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks/Details of Action")
    amicable_settlement_date = models.DateField(null=True, blank=True)
    agreement_details = models.TextField(blank=True, null=True, verbose_name="Amicable Settlement Agreement Details")

    def __str__(self):
        return f"Log for {self.case.blotter_id} on {self.date_processed.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-date_processed'] # Para ang pinakabago ang laging nasa taas

class Schedule(models.Model):
    case = models.ForeignKey(Blotter, on_delete=models.CASCADE, related_name='schedules')
    schedule_type = models.CharField(max_length=50) # 'Summon', 'Mediation', or 'Conciliation'
    appearance_date = models.DateField()
    appearance_time = models.TimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.schedule_type} for {self.case.blotter_id} on {self.appearance_date}"
    
    class Meta:
        ordering = ['-appearance_date', '-appearance_time']

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    related_blotter = models.ForeignKey(Blotter, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    related_report = models.ForeignKey(Report, on_delete=models.CASCADE, null=True, blank=True)

    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')

    def __str__(self):
        return f"Notification for {self.recipient.email}: {self.message[:30]}"
    
    class Meta:
        ordering = ['-timestamp']