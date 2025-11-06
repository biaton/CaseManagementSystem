from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .forms import OfficialSignUpForm
from cases.models import Blotter, Report, IncidentLog
from cases.choices import CASE_STATUS_CHOICES, INCIDENT_TYPE_CHOICES 
from django.contrib import messages
from users.models import CustomUser 
from django.db.models import Q
from audit_trail.models import AuditLog, OfficialNotification
from django.shortcuts import get_object_or_404 
from .forms import UpdateCaseStatusForm, ScheduleForm, AmicableSettlementForm, OfficialUpdateForm
from cases.models import Schedule
from itertools import chain
from django.contrib.auth.models import Group
from cases.choices import REPORT_STATUS_CHOICES
from .forms import UpdateReportStatusForm, QuickUpdateReportStatusForm, OfficialProfileUpdateForm
from .forms import OfficialPasswordResetRequestForm, OfficialVerifyOTPForm, OfficialSetNewPasswordForm
from cases.models import Notification
from django.http import JsonResponse
from cases.models import Schedule
from datetime import date, timedelta
from django.views.decorators.http import require_POST
from system_settings.models import LuponSchedule
from django.db.models import Count
from django.utils import timezone
from django.db.models.functions import TruncMonth
from system_settings.models import LuponMember, LuponAvailability
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
import random
import json

def group_required(*group_names):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name__in=group_names).exists() or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied
        return _wrapped_view
    return decorator

def is_barangay_tanod(user):
    # Check if the user is authenticated and belongs to the 'Barangay Tanod' group
    return user.is_authenticated and user.groups.filter(name='Barangay Tanod').exists()

def is_member_of_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()

def official_home_view(request):
    return render(request, 'official_portal/home.html')

# Ang decorator na ito ay para i-check kung naka-login at kung "staff" ba
def staff_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('official_login')
        
        # --- ITO ANG BAGONG CHECK ---
        # Pwede pa ring i-check ang is_staff, O mas specific, i-check ang group
        if not request.user.groups.filter(name='Officials').exists():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard') # Resident dashboard
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def custom_official_logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('official_login')

@staff_required
def official_dashboard_view(request):
    today = date.today()
    
    # 1. Stat Cards Data
    new_cases_count = Blotter.objects.filter(status='New').count()
    cases_today_count = Blotter.objects.filter(date_filed__date=today).count()
    resolved_cases_count = Blotter.objects.filter(status='Certified').count()
    resident_users_count = CustomUser.objects.filter(is_staff=False, is_active=True).count()

    # 2. Pie Chart Data (Cases by Incident Type)
    
    pie_chart_data = Blotter.objects.values('incident_type')\
        .annotate(count=Count('id')).order_by('-count')
    
    # I-map ang short value sa long display name
    incident_type_map = dict(INCIDENT_TYPE_CHOICES)
    pie_chart_labels = [incident_type_map.get(item['incident_type'], item['incident_type']) for item in pie_chart_data]
    pie_chart_values = [item['count'] for item in pie_chart_data]

    # 3. Column Chart Data (Monthly Case Volume)
    monthly_volume = Blotter.objects.filter(date_filed__year=today.year)\
        .annotate(month=TruncMonth('date_filed'))\
        .values('month').annotate(count=Count('id')).order_by('month')
    
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_values = [0] * 12
    for item in monthly_volume:
        month_index = item['month'].month - 1
        monthly_values[month_index] = item['count']

    # 4. Weekly Hearing Schedule Data
    start_of_week = today
    week_days = [start_of_week + timedelta(days=i) for i in range(7)]
    end_of_week = start_of_week + timedelta(days=6)
    
    schedules = Schedule.objects.filter(appearance_date__range=[start_of_week, end_of_week])\
        .select_related('case').order_by('appearance_time')
        
    grouped_schedules = {day: [] for day in week_days}
    for s in schedules:
        grouped_schedules[s.appearance_date].append(s)

    # 5. Lupon Availability Matrix for the week
    lupon_members = LuponMember.objects.filter(is_active=True)
    availability_data = LuponAvailability.objects.filter(lupon_member__in=lupon_members)
    
    availability_map = {}
    for avail in availability_data:
        if avail.lupon_member_id not in availability_map:
            availability_map[avail.lupon_member_id] = [False] * 5
        availability_map[avail.lupon_member_id][avail.day_of_week] = avail.is_available

    for member in lupon_members:
        member.availability = availability_map.get(member.id, [False] * 5)

    context = {
        'today_formatted': today.strftime("%A, %B %d, %Y"),
        'today': today,
        # Stat Cards
        'new_cases_count': new_cases_count,
        'total_cases_today_count': cases_today_count,
        'resolved_cases_count': resolved_cases_count,
        'registered_residents_count': resident_users_count,
        # Chart Data
        'pie_chart_labels': pie_chart_labels,
        'pie_chart_data': pie_chart_values,
        'column_chart_labels': month_labels,
        'column_chart_data': monthly_values,
        # Schedule Data
        'week_days': week_days,
        'grouped_schedules': grouped_schedules,

        'lupon_members_availability': lupon_members,
    }
    return render(request, 'official_portal/official_dashboard.html', context)

@staff_required
def add_official_view(request):
    if request.method == 'POST':
        form = OfficialSignUpForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get('password2') # UserCreationForm uses password2
            if not password:
                password = get_random_string(10) # Gumawa ng 10-character random password
            
            # I-save ang user pero HUWAG muna i-commit
            user = form.save(commit=False)
            
            # I-set ang password at iba pang details
            user.set_password(password)
            user.is_staff = True
            user.is_active = True
            user.is_verified = True
            
            # Isang beses lang i-save
            user.save() 

            password = form.cleaned_data.get('password')
            if not password:
                # Kung blangko, gumawa ng 8-character random password
                password = get_random_string(8)
            
            user.set_password(password) # Securely hashes the password
            user.is_active = True
            user.is_verified = True
            user.save()
            
            position_name = form.cleaned_data.get('barangay_position')

            try:
                officials_group = Group.objects.get(name='Officials')
                user.groups.add(officials_group)
            except Group.DoesNotExist:
                print("CRITICAL WARNING: 'Officials' group not found.")

            if position_name:
                try:
                    # Hanapin ang Group na may kaparehong pangalan
                    target_group = Group.objects.get(name=position_name)
                    # Idagdag ang user sa group na 'yon
                    user.groups.add(target_group)
                    messages.success(request, f"Official account for {user.email} created and assigned to '{position_name}' group.")
                except Group.DoesNotExist:
                    # Kung wala pang group na may ganoong pangalan
                    messages.warning(request, f"Account created, but the group '{position_name}' does not exist. Please create it in the admin panel.")
            else:
                 messages.success(request, f"Official account for {user.email} has been created successfully.")

            try:
                subject = "Your Official Account for the Barangay CMS is Ready!"
                html_message = render_to_string('official_portal/emails/new_official_welcome_email.html', {
                    'user': user,
                    'password': password, # Ipasa ang plain-text password
                })
                send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)
                messages.success(request, f"Official account created. Credentials sent to {user.email}.")
            except Exception as e:
                messages.warning(request, f"Account created, but failed to send email. Error: {e}")
                
            return redirect('manage_users')
    else:
        form = OfficialSignUpForm()
    
    context = {'form': form}
    return render(request, 'official_portal/add_official.html', context)

@staff_required
def approve_resident_view(request, pk):
    resident = get_object_or_404(CustomUser, pk=pk, is_staff=False)
    
    if request.method == 'POST':
        # Kung in-approve ng opisyal
        if 'approve' in request.POST:
            resident.is_active = True
            resident.save()

            subject = 'Your Barangay CMS Account has been Activated!'
            html_message = render_to_string(
                'official_portal/emails/account_activated_email.html', 
                {'user': resident}
            )
            
            send_mail(
                subject, 
                '', 
                settings.DEFAULT_FROM_EMAIL, 
                [resident.email], 
                fail_silently=False, 
                html_message=html_message
            )
            
            messages.success(request, f"Account for {resident.get_full_name()} has been approved and an email has been sent.")
        
            
            return redirect('manage_users')
        
        # Kung ni-reject (pwede nating i-delete o iwanang inactive)
        if 'reject' in request.POST:
            # For now, i-delete natin
            resident.delete()
            messages.warning(request, "The pending account has been rejected and deleted.")
            return redirect('manage_users')

    context = {'resident': resident}
    return render(request, 'official_portal/approve_resident.html', context)

@staff_required
def manage_users_view(request):
    search_query = request.GET.get('q', '')

    # Kunin ang lahat ng non-superuser accounts
    base_users = CustomUser.objects.filter(is_superuser=False).order_by('-date_joined')

    # I-filter base sa search query kung meron
    if search_query:
        base_users = base_users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    officials = base_users.filter(is_staff=True)
    residents = base_users.filter(is_staff=False) 

    context = {
        'officials': officials,
        'residents': residents,
        'officials_count': officials.count(),
        'resident_count': residents.count(), 
        'search_query': search_query,
    }
    return render(request, 'official_portal/manage_users.html', context)

@staff_required
def official_notification_list_view(request):
    # Kunin lahat ng notifications, pinakabago muna
    notifications = OfficialNotification.objects.all()
    
    # I-mark as read lahat ng unread notifications kapag binisita ang page
    # Ito ang mag-aalis ng numero sa badge
    unread_count = notifications.filter(is_read=False).count()
    if unread_count > 0:
        notifications.filter(is_read=False).update(is_read=True)
        messages.info(request, f"You have {unread_count} new notification(s).")

    context = {
        'notifications': notifications
    }
    return render(request, 'official_portal/official_notification_list.html', context)

@staff_required
def resident_profile_view(request, pk):
    # Kunin ang specific na resident, siguraduhing hindi ito staff
    resident = get_object_or_404(CustomUser, pk=pk, is_staff=False)
    
    # Kunin lahat ng cases na konektado sa resident na ito
    filed_blotters = Blotter.objects.filter(complainant=resident).order_by('-date_filed')
    filed_reports = Report.objects.filter(informant=resident).order_by('-date_filed')

    context = {
        'resident': resident,
        'filed_blotters': filed_blotters,
        'filed_reports': filed_reports,
    }
    return render(request, 'official_portal/resident_profile.html', context)

@staff_required
def edit_official_view(request, pk):
    # Kunin ang specific na official user
    official = get_object_or_404(CustomUser, pk=pk, is_staff=True)
    
    if request.method == 'POST':
        # I-pass ang 'instance=official' para malaman ng form na ito ay isang UPDATE, hindi CREATE
        form = OfficialUpdateForm(request.POST, instance=official)
        if form.is_valid():
            form.save()
            messages.success(request, f"Details for {official.get_full_name()} have been updated successfully.")
            return redirect('manage_users')
    else:
        # I-populate ang form ng existing data ng official
        form = OfficialUpdateForm(instance=official)

    context = {
        'form': form,
        'official': official
    }
    return render(request, 'official_portal/edit_official.html', context)

@staff_required
def deactivate_user_view(request, pk):
    # Siguraduhin na POST request lang
    if request.method == 'POST':
        # Kunin ang user na ide-deactivate
        user_to_deactivate = get_object_or_404(CustomUser, pk=pk)
        
        # Security check: Huwag payagan ang user na i-deactivate ang sarili niya
        if user_to_deactivate == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect('manage_users')

        # I-set ang is_active to False
        user_to_deactivate.is_active = False
        user_to_deactivate.save()
        
        messages.success(request, f"User {user_to_deactivate.get_full_name()} has been successfully deactivated.")
    else:
        messages.error(request, "Invalid request method.")
    
    return redirect('manage_users')

@staff_required
def records_list_view(request):
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    # Kunin lang ang Blotter records
    blotter_records = Blotter.objects.select_related('complainant').all().order_by('-date_filed')

    if search_query:
        blotter_records = blotter_records.filter(
            Q(blotter_id__icontains=search_query) |
            Q(complainant__first_name__icontains=search_query) |
            Q(complainant__last_name__icontains=search_query)
        )
    
    # Ang status filter ay para lang sa blotter
    if status_filter:
        blotter_records = blotter_records.filter(status=status_filter)
    
    context = {
        'blotter_records': blotter_records,
        'status_choices': CASE_STATUS_CHOICES, # Kailangan pa rin para sa filter dropdown
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'official_portal/records_list.html', context)

@staff_required
def incident_logs_view(request):
    search_query = request.GET.get('q', '')
    
    # Kunin ang lahat ng Blotter cases at i-prefetch ang related logs
    # para maiwasan ang maraming database queries sa loob ng loop.
    all_cases = Blotter.objects.select_related('complainant').prefetch_related('logs__processed_by').order_by('-date_filed')

    if search_query:
        all_cases = all_cases.filter(
            Q(blotter_id__icontains=search_query) |
            Q(incident_description__icontains=search_query) |
            Q(complainant__first_name__icontains=search_query) |
            Q(complainant__last_name__icontains=search_query)
        )

    for case in all_cases:
        # Kunin ang pinakabagong log
        last_log = case.logs.order_by('-date_processed').first()
        
        # Kunin ang pinakabagong log na may resulta
        last_log_with_result = case.logs.filter(result__isnull=False).order_by('-date_processed').first()

        # I-attach ang mga 'safe' values sa case object
        # Ito ang mag-aayos sa bug
        case.last_processed_by = last_log.processed_by if last_log else None
        case.last_processed_date = last_log.date_processed if last_log else case.date_filed
        case.final_result = last_log_with_result.result if last_log_with_result else "Unsettled"

    context = {
        'cases': all_cases,
        'search_query': search_query,
    }
    return render(request, 'official_portal/incident_logs.html', context)

@staff_required
def audit_trail_view(request):
    logs = AuditLog.objects.all()
    context = {'logs': logs}
    return render(request, 'official_portal/audit_trail.html', context)

@staff_required
def record_detail_view(request, pk):

    blotter = get_object_or_404(Blotter, pk=pk)
    schedules = blotter.schedules.all().order_by('-date_created') # Kunin ang history para sa display

    if request.method == 'POST':
        form = UpdateCaseStatusForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            remarks = form.cleaned_data['remarks']

            # Kung ang pinili ay isang step na nangangailangan ng schedule
            if new_status in ['Summon', 'Mediation', 'Conciliation']:
                # I-update muna ang status ng kaso
                blotter.status = new_status
                blotter.save()
                
                # Gumawa ng notification para sa complainant
                Notification.objects.create(
                    recipient=blotter.complainant,
                    related_blotter=blotter,
                    message=f"Your case ({blotter.blotter_id}) is now set for {new_status}. Please wait for the schedule details."
                )

                messages.info(request, f"Case status updated to '{new_status}'. You are now being redirected to set the schedule.")
                
                # I-redirect sa page kung saan pwedeng mag-set ng schedule
                return redirect('manage_proceedings', pk=blotter.pk)
            
            # Kung iba ang pinili (e.g., Dismiss, Certified), i-save lang at mag-log
            else:
                if not remarks:
                    messages.error(request, "Remarks are required for this action.")
                    # Manatili sa page para ma-correct ng user (hindi magre-redirect)
                else:
                    blotter.status = new_status
                    blotter.save()

                    # Gumawa ng log
                    IncidentLog.objects.create(
                        case=blotter,
                        case_title=f"Status changed to {new_status}",
                        incident_type="Status Update",
                        status=new_status,
                        processed_by=request.user,
                        remarks=remarks
                    )
                    
                    # Gumawa ng notification
                    Notification.objects.create(
                        recipient=blotter.complainant,
                        related_blotter=blotter,
                        message=f"An update on your case {blotter.blotter_id}: The status is now '{new_status}'."
                    )

                    try:
                        subject = f"Update on Your Case: {blotter.blotter_id}"
                        html_message = render_to_string('official_portal/emails/status_update_email.html', {
                            'user': blotter.complainant,
                            'case': blotter,
                            'new_status': new_status,
                            'remarks': remarks,
                        })
                        send_mail(
                            subject, '', settings.DEFAULT_FROM_EMAIL, [blotter.complainant.email],
                            fail_silently=False, html_message=html_message
                        )
                        messages.success(request, f"Case status updated to '{new_status}' and complainant has been notified.")
                    except Exception as e:
                        print(f"EMAIL SENDING FAILED (Status Update): {e}")
                        messages.warning(request, "Case status updated, but failed to send email notification to the complainant.")

                        messages.success(request, f"Case status successfully updated to '{new_status}'.")
                    return redirect('record_detail', pk=blotter.pk)
    
    # Kung GET request, o kung may error sa POST, ipakita ang form
    form = UpdateCaseStatusForm(initial={'status': blotter.status})

    context = {
        'blotter': blotter,
        'schedules': schedules, # Para sa history table sa template
        'form': form,           # Para sa 'Take Action' form
    }
    return render(request, 'official_portal/record_detail.html', context)

@staff_required
def report_detail_view(request, pk):
    report = get_object_or_404(Report.objects.select_related('informant'), pk=pk)

    if request.method == 'POST':
        form = UpdateReportStatusForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            action_taken = form.cleaned_data['action_taken']
            report.action_taken = action_taken
            report.status = new_status
            report.save()

            # 1. Gumawa ng portal notification
            Notification.objects.create(
                recipient=report.informant,
                message=f"An update on your report regarding '{report.report_details[:30]}...': The status is now '{report.get_status_display()}'.",
                related_report=report
            )

            # 2. Magpadala ng email notification
            try:
                subject = f"Update on Your General Report"
                html_message = render_to_string('official_portal/emails/report_status_update_email.html', {
                    'user': report.informant,
                    'report': report,
                })
                send_mail(
                    subject, '', settings.DEFAULT_FROM_EMAIL, [report.informant.email],
                    fail_silently=False, html_message=html_message
                )
                messages.success(request, "Report status updated and informant has been notified.")
            except Exception as e:
                print(f"EMAIL SENDING FAILED (Report Update): {e}")
                messages.warning(request, "Report status updated, but failed to send an email notification.")

            messages.success(request, f"Report status updated to '{new_status}'and action taken recorded.")
            return redirect('report_detail', pk=report.pk)
    else:
        form = UpdateReportStatusForm(initial={'status': report.status, 'action_taken': report.action_taken})

    context = {
        'report': report,
        'form': form,
    }
    return render(request, 'official_portal/report_detail.html', context)

@staff_required
def manage_proceedings_view(request, pk):
    case = get_object_or_404(Blotter, pk=pk)
    form = ScheduleForm() # I-define na natin ang form sa umpisa

    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.case = case
            schedule.created_by = request.user
            schedule.save()
            
            case.status = form.cleaned_data['schedule_type']
            case.save()

            IncidentLog.objects.create(
                case=case, case_title=f"{schedule.schedule_type} scheduled",
                incident_type="Scheduling", status=case.status,
                processed_by=request.user,
                remarks=f"Set for {schedule.appearance_date} at {schedule.appearance_time.strftime('%I:%M %p')}."
            )

            Notification.objects.create(
                recipient=case.complainant,
                related_blotter=case,
                message=f"A '{schedule.schedule_type}' has been scheduled for your case {case.blotter_id} on {schedule.appearance_date.strftime('%B %d, %Y')} at {schedule.appearance_time.strftime('%I:%M %p')}."
            )

            try:
                subject = f"Notice of {schedule.schedule_type} for Case: {case.blotter_id}"
                
                # Ihanda ang context para sa email template
                email_context = {
                    'case': case,
                    'schedule': schedule,
                }
                html_message = render_to_string('official_portal/emails/schedule_notification_email.html', email_context)
                
                # Ipadala ang email sa Complainant
                send_mail(
                    subject, '', settings.DEFAULT_FROM_EMAIL, [case.complainant.email],
                    fail_silently=False, html_message=html_message
                )

                # Opsyonal: Ipadala din sa Respondent kung may email siya
                # (Assume na wala pa tayong email field para sa respondent sa ngayon)
                
                messages.success(request, f"{schedule.schedule_type} has been scheduled and a notification has been sent to the complainant.")

            except Exception as e:
                print(f"EMAIL SENDING FAILED (Schedule Notification): {e}")
                messages.warning(request, f"{schedule.schedule_type} was scheduled, but failed to send email notifications.")
            return redirect('manage_proceedings', pk=case.pk)
        
    # Ihiwalay ang schedules base sa type para sa mas madaling display
    all_schedules = case.schedules.all()
    summons = all_schedules.filter(schedule_type='Summon')
    mediations = all_schedules.filter(schedule_type='Mediation')
    conciliations = all_schedules.filter(schedule_type='Conciliation')

    combined_schedules = sorted(
        list(chain(summons, mediations, conciliations)),
        key=lambda x: x.appearance_date,
        reverse=True
    )

    context = {
        'case': case,
        'form': form,
        'summons': summons,
        'mediations': mediations,
        'conciliations': conciliations,
        'all_schedules': combined_schedules,
    }

    return render(request, 'official_portal/manage_proceedings.html', context)

@staff_required
def create_amicable_settlement_view(request, case_pk):
    """
    Handles the creation of an Amicable Settlement,
    updates the case status, logs the action, and notifies the complainant.
    """
    case = get_object_or_404(Blotter, pk=case_pk)

    if request.method == 'POST':
        form = AmicableSettlementForm(request.POST)
        if form.is_valid():
            settlement_date = form.cleaned_data['amicable_settlement_date']
            agreement = form.cleaned_data['agreement_details']

            # Step 1: I-update ang status ng case to 'Certified' dahil tapos na
            case.status = 'Certified'
            case.save()

            # Step 2: Gumawa ng final Incident Log para i-record ang settlement
            IncidentLog.objects.create(
                case=case,
                case_title="Amicable Settlement Reached",
                incident_type="Settlement",
                status="Certified",
                result="Settled",  # Ang RESULTA ng kaso ay 'Settled'
                processed_by=request.user,
                amicable_settlement_date=settlement_date,
                agreement_details=agreement,
                remarks="The case has been formally settled by both parties and is now certified closed."
            )
            
            # --- ITO ANG EMAIL SENDING LOGIC (na may debugging) ---
            # Aalisin natin ang try...except para makita ang totoong error
            
            subject = f"Your Case Has Been Settled: {case.blotter_id}"
            html_message = render_to_string(
                'official_portal/emails/settlement_email.html', 
                {
                    'user': case.complainant,
                    'case': case,
                    'agreement': agreement,
                }
            )
            
            send_mail(
                subject, 
                '', # Plain text message (optional since we use HTML)
                settings.DEFAULT_FROM_EMAIL, 
                [case.complainant.email],
                fail_silently=False, 
                html_message=html_message
            )
            
            # Kung walang error, ito ang magiging message
            messages.success(request, "Amicable Settlement recorded and complainant has been notified by email.")
            
            return redirect('record_detail', pk=case.pk)
    else:
        # Kung GET request, gumawa lang ng blangkong form
        form = AmicableSettlementForm()

    context = {
        'case': case,
        'form': form,
    }
    return render(request, 'official_portal/create_settlement.html', context)

@staff_required
def quick_update_report_status_view(request, pk):
    report = get_object_or_404(Report, pk=pk)
    
    # Alamin kung saan nanggaling ang request
    redirect_url = request.POST.get('next', 'list_records') # Default pabalik sa main records

    if request.method == 'POST':
        form = QuickUpdateReportStatusForm(request.POST)
        if form.is_valid():
            report.status = form.cleaned_data['status']
            report.save()
            messages.success(request, f"Status for report from '{report.informant.get_full_name()}' updated successfully.")
        else:
            messages.error(request, "Invalid status selected.")

            # 1. Portal Notification
            Notification.objects.create(
                recipient=report.informant,
                message=f"The status of your report ('{report.report_details[:30]}...') has been updated to '{report.get_status_display()}'."
            )

            # 2. Email Notification
            try:
                # (Yung buong try...except block para sa email, kopyahin mo rin dito)
                subject = ...
                html_message = render_to_string(...)
                send_mail(...)
                messages.success(request, f"Report status updated and informant notified.")
            except Exception as e:
                messages.warning(request, "Report status updated, but failed to send email.")
    
    return redirect(redirect_url)

@staff_required
def delete_blotter_view(request, pk):
    # Siguraduhin na POST request lang ang tinatanggap para sa security
    if request.method == 'POST':
        blotter = get_object_or_404(Blotter, pk=pk)
        blotter_id = blotter.blotter_id # I-save ang ID para sa message
        blotter.delete()
        messages.success(request, f"Blotter case {blotter_id} has been successfully deleted.")
    else:
        # Kung hindi POST, i-redirect lang
        messages.error(request, "Invalid request method.")
    
    # Laging i-redirect pabalik sa records list
    return redirect('list_records')

@staff_required
def lupon_schedule_view(request):
    # Kunin lang ang mga opisyal na may position na 'Lupong Tagapamayapa Member'
    lupon_members = CustomUser.objects.filter(
        barangay_position='Lupong Tagapamayapa Member', 
        is_active=True
    ).order_by('last_name')
    
    # Kunin ang existing schedules
    schedules = LuponSchedule.objects.all()

    # I-prepare ang data para sa template
    schedule_data = {}
    for schedule in schedules:
        if schedule.lupon_member_id not in schedule_data:
            schedule_data[schedule.lupon_member_id] = {}
        schedule_data[schedule.lupon_member_id][schedule.day_of_week] = schedule.is_available

    # I-attach ang availability sa bawat member
    for member in lupon_members:
        member.availability = [schedule_data.get(member.id, {}).get(day, False) for day in range(5)]

    context = {
        'lupon_members': lupon_members,
        'days_of_week': range(5), 
    }
    return render(request, 'official_portal/lupon_schedule.html', context)

@staff_required
@require_POST
def update_lupon_schedule_api(request):
    try:
        data = json.loads(request.body)
        lupon_id = data.get('lupon_id')
        day_index = data.get('day_index')
        is_available = data.get('is_available')

        lupon_member = CustomUser.objects.get(pk=lupon_id)
        
        schedule, created = LuponSchedule.objects.update_or_create(
            lupon_member=lupon_member,
            day_of_week=day_index,
            defaults={'is_available': is_available}
        )
        return JsonResponse({'status': 'success', 'message': 'Schedule updated.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_required
def official_profile_view(request):
    user = request.user
    
    if request.method == 'POST':
        form = OfficialProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('official_profile')
    else:
        form = OfficialProfileUpdateForm(instance=user)

    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'official_portal/official_profile.html', context)

@staff_required
def official_change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  
            messages.success(request, "Your password was successfully updated.")
            return redirect('official_change_password') 
        else:
            messages.error(request, "Please correct the password errors below.")
    else:
        form = PasswordChangeForm(request.user)

    context = {'form': form}
    return render(request, 'official_portal/official_change_password.html', context)

def request_password_reset_official(request):
    if request.method == 'POST':
        form = OfficialPasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                # Siguraduhing official (is_staff=True) ang user
                user = CustomUser.objects.get(email=email, is_staff=True)
                otp = str(random.randint(100000, 999999))
                user.otp = otp
                user.otp_created_at = timezone.now()
                user.save()

                # Send email (gagamit ng ibang template)
                send_mail('Official Portal - Password Reset OTP', f'Your OTP is: {otp}', settings.DEFAULT_FROM_EMAIL, [user.email])
                
                request.session['reset_email_official'] = email
                messages.success(request, 'An OTP has been sent to your official email.')
                return redirect('official_password_reset_verify')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No official account found with that email address.')
    else:
        form = OfficialPasswordResetRequestForm()
    return render(request, 'official_portal/password_reset/request.html', {'form': form})

def verify_otp_official(request):
    email = request.session.get('reset_email_official')
    if not email: return redirect('official_password_reset_request')

    if request.method == 'POST':
        form = OfficialVerifyOTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            try:
                user = CustomUser.objects.get(email=email, otp=otp, is_staff=True)
                if user.is_otp_valid():
                    request.session['otp_verified_email_official'] = email
                    user.otp = None; user.otp_created_at = None; user.save()
                    return redirect('official_password_reset_set_new')
                else:
                    messages.error(request, 'OTP has expired.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'Invalid OTP.')
    else:
        form = OfficialVerifyOTPForm()
    return render(request, 'official_portal/password_reset/verify.html', {'form': form})

def set_new_password_official(request):
    email = request.session.get('otp_verified_email_official')
    if not email: return redirect('official_password_reset_request')

    if request.method == 'POST':
        form = OfficialSetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user = CustomUser.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            del request.session['reset_email_official']
            del request.session['otp_verified_email_official']

            messages.success(request, 'Password has been reset successfully. You can now log in.')
            return redirect('official_login')
    else:
        form = OfficialSetNewPasswordForm()
    return render(request, 'official_portal/password_reset/set_new.html', {'form': form})

@login_required
def notify_secretary_view(request, pk):
    blotter = get_object_or_404(Blotter, pk=pk)

    # Optional: You might want to restrict this view only to Barangay Tanod
    # You can use the `is_member_of_group` helper function or a custom decorator
    if not is_member_of_group(request.user, 'Barangay Tanod'):
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('official_portal:record_detail', pk=blotter.pk) # Redirect if not authorized

    if request.method == 'POST':
        try:
            # Hanapin ang Barangay Secretary user
            # Assuming mayroon kang user sa group na 'Barangay Secretary'
            secretary_group = Group.objects.get(name='Barangay Secretary')
            # Kunin ang lahat ng user sa group na ito (pwede mong piliin ang una kung isang secretary lang)
            secretary_users = secretary_group.user_set.filter(is_active=True)

            if secretary_users.exists():
                # Pwede mong piliin ang unang secretary o mag-notify sa lahat ng secretary
                secretary_user = secretary_users.first() 
                
                # Check if a similar notification already exists to avoid spamming
                existing_notification = Notification.objects.filter(
                    recipient=secretary_user,
                    related_blotter=blotter,
                    message__icontains="needs review by the Secretary", # Pwede mong ayusin ang message
                    sender=request.user # Kung may sender field ka sa Notification model
                ).first()

                if not existing_notification:
                    # Gumawa ng notification para sa Barangay Secretary
                    Notification.objects.create(
                        recipient=secretary_user,
                        sender=request.user, # Ang Tanod na nag-notify
                        message=f"Blotter Case {blotter.blotter_id} ({blotter.get_incident_type_display()}) needs review by the Secretary. Submitted by {blotter.complainant.get_full_name()}.",
                        related_blotter=blotter # I-link ang blotter
                    )
                    messages.success(request, f"Barangay Secretary has been notified about Case {blotter.blotter_id} for review.")

                    try:
                        subject = f"ACTION REQUIRED: Blotter Case {blotter.blotter_id} for Review"
                
                        html_message = render_to_string('official_portal/emails/secretary_review_email.html', {
                            'secretary_user': secretary_user,
                            'blotter': blotter,
                            'tanod_notified_by': request.user,
                            'request': request, 
                        })
                
                        send_mail(
                            subject,
                            # Ito ang plain text version ng email kung hindi ma-render ang HTML
                            f"Blotter Case {blotter.blotter_id} ({blotter.get_incident_type_display()}) needs your review. Filed by {blotter.complainant.get_full_name()}. Notified by {request.user.get_full_name()}.",
                            settings.DEFAULT_FROM_EMAIL,
                            [secretary_user.email],
                            fail_silently=False,
                            html_message=html_message 
                        )
                        messages.success(request, "Email notification sent to Barangay Secretary.")
                    except Exception as e:
                        print(f"EMAIL SENDING FAILED (Secretary Notification): {e}")
                        messages.warning(request, "Email notification to Barangay Secretary failed to send.") # <-- Ilipat DITO!

                else: # Kung may existing notification na
                    messages.info(request, f"Barangay Secretary has already been notified about Case {blotter.blotter_id} by {request.user.get_full_name()}.")
            else: # Kung walang secretary user na nakita
                messages.error(request, "No active Barangay Secretary user found to notify.")


        except Group.DoesNotExist:
            messages.error(request, "Error: 'Barangay Secretary' group does not exist. Please create this group in Django admin.")
        except CustomUser.DoesNotExist: # Assuming secretary_user could be CustomUser if you are using get_object_or_404
            messages.error(request, "Error: Barangay Secretary user not found within the group. Please check user assignments.")
        except Exception as e:
            print(f"AN UNEXPECTED ERROR OCCURRED IN NOTIFY_SECRETARY_VIEW: {e}")
            messages.error(request, f"An unexpected error occurred: {e}")

    return redirect('record_detail', pk=blotter.pk)