from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import OnSiteBlotterForm, OnSiteReportForm
from users.models import CustomUser # Para sa paggawa ng dummy user
from cases.models import Notification, Blotter, Report   # Ang totoong Blotter model
from cases.choices import REPORT_STATUS_CHOICES
from django.db.models import Q
from cases.choices import CASE_STATUS_CHOICES
from official_portal.views import group_required
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from cases.models import Notification, Blotter
from users.models import CustomUser
from django.utils.html import strip_tags

@login_required
def create_onsite_blotter_view(request):
    if request.method == 'POST':
        form = OnSiteBlotterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Step 1: Gawa (o hanapin) ang "dummy" user account para sa complainant
            # Gagamit tayo ng unique email para maiwasan ang conflict
            first_name_slug = data['complainant_first_name'].lower().replace(' ', '')
            last_name_slug = data['complainant_last_name'].lower().replace(' ', '')
            dummy_email = f"onsite.{first_name_slug}.{last_name_slug}@barangay.local"
            
            complainant_user, created = CustomUser.objects.get_or_create(
                email=dummy_email,
                defaults={
                    'first_name': data['complainant_first_name'],
                    'last_name': data['complainant_last_name'],
                    'middle_name': data.get('complainant_middle_name', ''),
                    'suffix': data.get('complainant_suffix', ''),
                    'address': data['complainant_address'],
                    'phone_number': data['complainant_contact_number'],
                    'is_active': False, # Para hindi sila maka-login
                    'is_staff': False,
                }
            )

            # Step 2: Gumawa na ng Blotter instance gamit ang complainant_user
            blotter_case = Blotter.objects.create(
                complainant=complainant_user,
                complainant_contact_number=data['complainant_contact_number'],
                incident_type=data['incident_type'],
                date_of_incident=data['date_of_incident'],
                location_of_incident=data['location_of_incident'],
                incident_description=data['incident_description'],
                respondent_first_name=data['respondent_first_name'],
                respondent_last_name=data['respondent_last_name'],
                respondent_middle_name=data.get('respondent_middle_name', ''),
                respondent_address=data['respondent_address'],
                # Ang status at blotter_id ay automatic nang mase-set ng model's save() method
            )

            messages.success(request, f"On-site blotter record ({blotter_case.blotter_id}) has been created and added to the main records.")
            return redirect('onsite_reports:hub')
    else:
        form = OnSiteBlotterForm()

    context = {'form': form}
    return render(request, 'onsite_reports/create_onsite_blotter.html', context)

@login_required
def create_onsite_report_view(request):
    if request.method == 'POST':
        form = OnSiteReportForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Step 1: Gawa (o hanapin) ang "dummy" user para sa informant
            first_name_slug = data['informant_first_name'].lower().replace(' ', '')
            last_name_slug = data['informant_last_name'].lower().replace(' ', '')
            dummy_email = f"onsite_report.{first_name_slug}.{last_name_slug}@barangay.local"
            
            informant_user, created = CustomUser.objects.get_or_create(
                email=dummy_email,
                defaults={
                    'first_name': data['informant_first_name'],
                    'last_name': data['informant_last_name'],
                    'phone_number': data['informant_contact_number'],
                    'is_active': False,
                }
            )

            # Step 2: Gumawa ng Report instance
            Report.objects.create(
                informant=informant_user,
                informant_contact_number=data['informant_contact_number'],
                date_of_incident=data['date_of_incident'],
                location_of_incident=data['location_of_incident'],
                report_details=data['report_details'],
            )

            messages.success(request, f"On-site report has been successfully created.")
            return redirect('onsite_reports:hub')
    else:
        form = OnSiteReportForm()

    context = {'form': form}
    return render(request, 'onsite_reports/create_onsite_report.html', context)

@login_required
def view_onsite_blotters_view(request):
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '') # Idagdag ang status filter
    
    # Kunin lahat ng Blotters at i-order by pinakabago
    blotters = Blotter.objects.select_related('complainant').all().order_by('-date_filed')
    
    if search_query:
        blotters = blotters.filter(
            Q(blotter_id__icontains=search_query) |
            Q(complainant__first_name__icontains=search_query) |
            Q(complainant__last_name__icontains=search_query)
        )
    
    # Idagdag ang filtering by status
    if status_filter:
        blotters = blotters.filter(status=status_filter)

    context = {
        'blotter_records': blotters, # Palitan to blotter_records para consistent
        'status_choices': CASE_STATUS_CHOICES, # Ipasa ang choices para sa filter
        'search_query': search_query,
        'status_filter': status_filter
    }
    return render(request, 'onsite_reports/view_blotters.html', context)


@login_required
def view_onsite_reports_view(request):
    search_query = request.GET.get('q', '')
    
    reports = Report.objects.select_related('informant').all().order_by('-date_filed')
    
    if search_query:
        reports = reports.filter(
            Q(informant__first_name__icontains=search_query) |
            Q(informant__last_name__icontains=search_query) |
            Q(report_details__icontains=search_query)
        )

    context = {
        'records': reports,
        'status_choices_reports': REPORT_STATUS_CHOICES, # Para sa dropdown ng modal
        'search_query': search_query
    }
    return render(request, 'onsite_reports/view_reports.html', context)

@login_required
def blotter_detail_view(request, pk):
    OnSiteBlotterForm = get_object_or_404(Blotter, pk=pk)
    if request.method == 'POST':
        form = OnSiteBlotterForm(request.POST, request.FILES)
        if form.is_valid():
            blotter_instance = form.save(commit=False)
            blotter_instance.complainant = request.user
            blotter_instance.save()
            messages.success(request, f'Blotter successfully filed! Your Blotter ID is {blotter_instance.blotter_id}.')

            # --- Notification para sa Complainant (Resident) ---
            # Ito ay para sa resident na ang complainant
            Notification.objects.create(
                recipient=request.user, # The complainant (whoever created it)
                message=f"Your blotter case (ID: {blotter_instance.blotter_id}) has been successfully filed and is awaiting review.",
                related_blotter=blotter_instance
            )

            # --- Logic para sa Barangay Secretary (Notification at Email) ---
            try:
                secretary_group = Group.objects.get(name='Barangay Secretary')
                barangay_secretaries = CustomUser.objects.filter(groups=secretary_group, is_active=True)

                for secretary in barangay_secretaries:
                    Notification.objects.create(
                        recipient=secretary,
                        message=f"New Blotter Case Filed: {blotter_instance.blotter_id} by {blotter_instance.complainant.get_full_name()}.",
                        related_blotter=blotter_instance
                    )

                    if secretary.email:
                        subject = f"New Blotter Case Filed: {blotter_instance.blotter_id}"
                        html_message = render_to_string('emails/new_blotter_notification_secretary.html', {
                            'secretary': secretary,
                            'blotter': blotter_instance,
                            'complainant': blotter_instance.complainant,
                            # 'blotter_link': request.build_absolute_uri(reverse('official_portal:blotter_detail', kwargs={'pk': blotter_instance.pk}))
                        })
                        try:
                            send_mail(
                                subject,
                                strip_tags(html_message),
                                settings.DEFAULT_FROM_EMAIL,
                                [secretary.email],
                                fail_silently=False,
                                html_message=html_message,
                            )
                            print(f"Email sent to {secretary.email} for new blotter.")
                        except Exception as e:
                            print(f"Failed to send email to {secretary.email} for new blotter: {e}")

            except Group.DoesNotExist:
                print("WARNING: 'Barangay Secretary' group does not exist. No notification/email sent to secretary.")
            except Exception as e:
                print(f"Error sending secretary notification/email for new blotter: {e}")

            return redirect('official_portal:blotter_list') # Redirect to an official's blotter list
        
    else:
        form = OnSiteBlotterForm()

    context = {'form': form}
    return render(request, 'official_portal/create_blotter.html', context)

@login_required 
def reporting_hub_view(request):
    context = {}
    return render(request, 'onsite_reports/hub.html', context)