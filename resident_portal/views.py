from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from .forms import ResidentProfileUpdateForm ,ResidentSignUpForm, BlotterForm, ReportForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from announcements.models import Announcement
from system_settings.models import Hotline, ExternalLink, Contact
from cases.models import Notification, Blotter, Report, Schedule, Case 
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from datetime import date, timedelta
from users.models import CustomUser 
from cases.choices import INCIDENT_TYPE_CHOICES
from django.utils import timezone 
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from system_settings.models import OfficialDisplay
from .forms import PasswordResetRequestForm, VerifyOTPForm, SetNewPasswordForm
from django.contrib.auth.hashers import make_password
from system_settings.models import Contact
from audit_trail.models import OfficialNotification
import random
import calendar
import json


# --- Public View ---
def public_home_view(request):
    hotlines = Hotline.objects.all()
    links = ExternalLink.objects.all()
    contacts = Contact.objects.all().order_by('name')
    
    context = {
        'display_hotlines_list': hotlines,
        'display_other_links': links,
        'display_other_contacts': contacts,
         
    }
    return render(request, 'resident_portal/public_home.html', context)

def signup_view(request):
    if request.method == 'POST':

        print("--- SIGNUP POST REQUEST RECEIVED ---")
        print("request.POST data:", request.POST)
        print("request.FILES data:", request.FILES)
        print("---------------------------------") 

        form = ResidentSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 
            user.save()

            form.save_m2m()

            user.groups.add(Group.objects.get(name='Residents'))
            
            try:
                residents_group = Group.objects.get(name='Residents')
                user.groups.add(residents_group)
            except Group.DoesNotExist:
                print("CRITICAL WARNING: 'Residents' group not found in the database.")

            # Mag-create ng notification para sa admin
            try:
                approval_url = request.build_absolute_uri(
                    reverse('approve_resident', kwargs={'pk': user.pk})
                )
                OfficialNotification.objects.create(
                    message=f"New resident '{user.get_full_name()}' is pending for approval.",
                    link=approval_url
                )
            except Exception as e:
                print(f"Failed to create official notification: {e}")

            # 4. Magpakita ng tamang success message
            messages.success(request, 'Registration successful! Your account is now pending for approval by a barangay official. You will be notified via email once it is activated.')

            return redirect('resident_portal:login')
        
        else:
            print("--- SIGNUP FORM ERRORS ---")
            print(form.errors.as_json())
            print("--------------------------")
            
            messages.error(request, "Registration failed. Please check the errors below and try again.")

    else:
        form = ResidentSignUpForm()
    
    context = {'form': form}
    return render(request, 'resident_portal/signup.html', context)

def request_password_reset_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                # Generate a 6-digit OTP
                otp = str(random.randint(100000, 999999))
                user.otp = otp
                user.otp_created_at = timezone.now()
                user.save()

                # Send the OTP via email
                subject = 'Your Password Reset OTP'
                message = f'Hi {user.first_name}, your One-Time Password (OTP) for password reset is: {otp}. It is valid for 5 minutes.'
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                
                # I-store ang email sa session para sa next step
                request.session['reset_email'] = email
                messages.success(request, 'An OTP has been sent to your email.')
                return redirect('resident_portal:verify_otp')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No user found with that email address.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'resident_portal/password_reset/request.html', {'form': form})


def verify_otp_view(request):
    email = request.session.get('reset_email')
    if not email: return redirect('resident_portal:password_reset_request')

    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            try:
                user = CustomUser.objects.get(email=email, otp=otp)
                if user.is_otp_valid():
                    request.session['otp_verified_email'] = email
                    # Linisin ang OTP para hindi na magamit ulit
                    user.otp = None
                    user.otp_created_at = None
                    user.save()
                    return redirect('resident_portal:set_new_password')
                else:
                    messages.error(request, 'OTP has expired. Please request a new one.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = VerifyOTPForm()
    return render(request, 'resident_portal/password_reset/verify.html', {'form': form})


def set_new_password_view(request):
    email = request.session.get('otp_verified_email')
    if not email: return redirect('resident_portal:password_reset_request')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user = CustomUser.objects.get(email=email)
            user.set_password(new_password) # Securely hashes the password
            user.save()
            
            # Linisin ang session
            del request.session['reset_email']
            del request.session['otp_verified_email']

            messages.success(request, 'Your password has been successfully reset! You can now log in.')
            return redirect('resident_portal:login')
    else:
        form = SetNewPasswordForm()
    return render(request, 'resident_portal/password_reset/set_new.html', {'form': form})

def help_center_view(request):
    # Kunin natin ang mga importanteng contacts para i-display
    contacts = Contact.objects.all()
    
    context = {
        'contacts': contacts
    }
    return render(request, 'resident_portal/help_center.html', context)

@login_required
def dashboard_view(request):
    
    
    today = timezone.now().date()
    
    # --- DATA PARA SA STATS CARDS (Personal sa User) ---
    user_cases = Blotter.objects.filter(complainant=request.user) # Pinalitan ang Case to Blotter at reporter to complainant
    total_cases_filed = user_cases.count()
    ongoing_cases_count = user_cases.exclude(Q(status='Certified') | Q(status='Dismissed')).count()
    settled_cases_count = user_cases.filter(status='Certified').count()

    # --- DATA PARA SA CHARTS (Galing sa LAHAT ng Kaso) ---
    all_cases = Blotter.objects.all() # Kukunin natin lahat ng kaso sa buong barangay

    # PIE CHART DATA (galing sa lahat ng kaso)
    type_counts = all_cases.values('incident_type').annotate(count=Count('incident_type')).order_by('-count')
    type_display_map = dict(INCIDENT_TYPE_CHOICES) 
    pie_chart_labels = [type_display_map.get(item['incident_type']) for item in type_counts]
    pie_chart_data = [item['count'] for item in type_counts]

    # COLUMN CHART DATA (galing sa lahat ng kaso)
    monthly_counts = all_cases.annotate(month=TruncMonth('date_filed')).values('month').annotate(count=Count('id')).order_by('month')
    month_data = {i: 0 for i in range(1, 13)}
    for entry in monthly_counts:
        month_data[entry['month'].month] = entry['count']
    column_chart_labels = [calendar.month_abbr[i] for i in range(1, 13)]
    column_chart_data = list(month_data.values())

    today = timezone.now().date()

    # --- Ipasa lahat ng data sa template ---
    context = {
        # Personal Stats
        'total_cases_filed': total_cases_filed,
        'ongoing_cases_count': ongoing_cases_count,
        'settled_cases_count': settled_cases_count,
        
        # Barangay-wide Chart Data
        'pie_chart_labels': pie_chart_labels,
        'pie_chart_data': pie_chart_data,
        'column_chart_labels': column_chart_labels,
        'column_chart_data': column_chart_data,
        'today_formatted': timezone.now().strftime("%A, %B %d, %Y"),
    }
    return render(request, 'resident_portal/dashboard.html', context)

@login_required
def create_blotter_view(request):
    if request.method == 'POST':
        form = BlotterForm(request.POST, request.FILES) # Add request.FILES for image
        if form.is_valid():
            blotter_instance = form.save(commit=False)
            blotter_instance.complainant = request.user # Set ang complainant sa logged-in user
            blotter_instance.save()
            messages.success(request, f'Blotter successfully filed! Your Blotter ID is {blotter_instance.blotter_id}.')

            Notification.objects.create(
                recipient=request.user, # Sino ang makakatanggap ng notification (dapat recipient, hindi user)
                message=f"Your blotter case (ID: {blotter_instance.blotter_id}) has been successfully filed and is awaiting review.",
                related_blotter=blotter_instance # I-link ang Blotter object dito
            )

            return redirect('resident_portal:resident_case_detail', pk=blotter_instance.pk)
    else:
        form = BlotterForm()

    context = {'form': form}
    return render(request, 'resident_portal/create_blotter.html', context)

@login_required
def create_report_view(request):
    if request.method == 'POST':
        form = ReportForm(request.POST) # Walang request.FILES dito dahil wala tayong image upload
        if form.is_valid():
            report_instance = form.save(commit=False)
            report_instance.informant = request.user
            report_instance.save()
            messages.success(request, 'Your report has been successfully filed.')

            Notification.objects.create(
                recipient=request.user, # Sino ang makakatanggap ng notification
                message=f"Your general report (ID: {report_instance.pk}) has been successfully submitted.",
                related_report=report_instance # I-link ang Report object dito
            )

            return redirect('resident_portal:resident_report_detail', pk=report_instance.pk)
    else:
        form = ReportForm()

    context = {'form': form}
    return render(request, 'resident_portal/create_report.html', context)

@login_required 
def my_schedules_view(request):
    user = request.user
    today = date.today()
    
    # Kunin ang Lunes ng kasalukuyang linggo
    start_of_week = today - timedelta(days=today.weekday())
    
    # Kunin ang mga araw mula Lunes hanggang Biyernes
    week_days = [start_of_week + timedelta(days=i) for i in range(5)]
    end_of_week = start_of_week + timedelta(days=4)

    # Kunin ang lahat ng schedules ng user para sa linggong ito
    schedules = Schedule.objects.filter(
        case__complainant=user,
        appearance_date__range=[start_of_week, end_of_week]
    ).select_related('case').order_by('appearance_time')

    # I-group ang schedules by day
    grouped_schedules = {day: [] for day in week_days}
    for s in schedules:
        if s.appearance_date in grouped_schedules:
            grouped_schedules[s.appearance_date].append(s)
    
    context = {
        'week_days': week_days,
        'grouped_schedules': grouped_schedules,
    }
    return render(request, 'resident_portal/my_schedules.html', context)


def announcement_list_view(request):
    announcements = Announcement.objects.filter(is_published=True).order_by('-date_published')
    context = { 'announcements': announcements }
    # Palitan ang pangalan ng template dito
    return render(request, 'resident_portal/resident_announcement_list.html', context)

# --- ITO ANG BAGO ---
def announcement_detail_view(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, is_published=True)
    
    # Opsyonal: Kunin ang 3 pinakabagong announcements maliban sa current
    other_announcements = Announcement.objects.filter(is_published=True).exclude(pk=pk)[:3]

    context = {
        'announcement': announcement,
        'other_announcements': other_announcements
    }
    return render(request, 'resident_portal/resident_announcement_detail.html', context)

@login_required
def notification_list_view(request):
    # Kunin lahat ng notifications ng user
    notifications = Notification.objects.filter(recipient=request.user)
    
    # I-mark as read lahat ng unread pag bisita sa page
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)

    context = {'notifications': notifications}
    return render(request, 'resident_portal/notification_list.html', context)

@login_required
def my_cases_hub_view(request):
    """
    Ito ang bagong Hub. Nagpapakita lang ng buttons na may counts.
    """
    user = request.user
    
    # Bilangin kung ilan ang bawat isa
    blotter_count = Blotter.objects.filter(complainant=user).count()
    report_count = Report.objects.filter(informant=user).count()

    context = {
        'blotter_count': blotter_count,
        'report_count': report_count,
    }
    return render(request, 'resident_portal/my_cases_hub.html', context)


@login_required
def my_blotters_list_view(request):
    """
    Ito ay dedicated page para lang sa listahan ng Blotters ng user.
    """
    blotters = Blotter.objects.filter(complainant=request.user).order_by('-date_filed')
    context = {'blotters': blotters}
    return render(request, 'resident_portal/my_blotters_list.html', context)


@login_required
def my_reports_list_view(request):
    """
    Ito ay dedicated page para lang sa listahan ng General Reports ng user.
    """
    reports = Report.objects.filter(informant=request.user).order_by('-date_filed')
    context = {'reports': reports}
    return render(request, 'resident_portal/my_reports_list.html', context)

@login_required
def report_summary_view(request, pk):
    # Siguraduhin na ang case ay para sa naka-login na user lang
    case = get_object_or_404(Blotter, pk=pk, complainant=request.user)
    # Kunin din natin ang history ng logs para sa case na ito
    logs = case.logs.all().order_by('-date_processed')
    
    context = {
        'case': case,
        'logs': logs,
    }
    return render(request, 'resident_portal/report_summary.html', context)

@login_required
def blotter_paper_view(request, pk):
    case = get_object_or_404(Blotter, pk=pk, complainant=request.user)
    context = {'blotter': case} # Ginawang 'blotter' para ma-reuse ang template
    # I-re-reuse natin ang 'record_detail.html' pero gagawa tayo ng resident version
    return render(request, 'resident_portal/blotter_paper.html', context)

@login_required
def hearing_schedule_view(request, pk):
    case = get_object_or_404(Blotter, pk=pk, complainant=request.user)
    schedules = case.schedules.all().order_by('appearance_date', 'appearance_time')
    context = {
        'case': case,
        'schedules': schedules,
    }
    return render(request, 'resident_portal/hearing_schedule.html', context)

@login_required
def resident_report_detail_view(request, pk):
    # Siguraduhin na ang report ay para sa naka-login na user lang
    report = get_object_or_404(Report, pk=pk, informant=request.user)
    
    context = {
        'report': report,
    }
    return render(request, 'resident_portal/resident_report_detail.html', context)

@login_required
def resident_case_detail_view(request, pk):
    # Kunin ang blotter, siguraduhing pag-aari ito ng naka-login na user
    blotter = get_object_or_404(Blotter, pk=pk, complainant=request.user)
    
    # Ang template na ang bahalang kumuha ng .logs.all
    context = {
        'blotter': blotter,
    }
    return render(request, 'resident_portal/resident_case_detail.html', context)

@login_required
def profile_settings_view(request):
    # I-initialize ang parehong forms
    profile_form = ResidentProfileUpdateForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    
    # Check kung ang na-submit ay ang PROFILE form
    if request.method == 'POST' and 'update_profile' in request.POST:
        profile_form = ResidentProfileUpdateForm(request.POST, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('resident_portal:profile_settings')

    # Check kung ang na-submit ay ang PASSWORD form
    if request.method == 'POST' and 'change_password' in request.POST:
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Importante para hindi ma-logout ang user
            messages.success(request, "Your password was successfully updated.")
            return redirect('resident_portal:profile_settings')
        else:
            messages.error(request, "Please correct the password errors below.")
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form
    }
    return render(request, 'resident_portal/profile_settings.html', context)

def about_us_view(request):
    officials = OfficialDisplay.objects.all().order_by('order')

    context = {
        'officials': officials
    }
    return render(request, 'resident_portal/about_us.html', context)

@login_required
def resident_help_center_view(request):
    context = {}
    return render(request, 'resident_portal/resident_help_center.html', context)