from django.urls import path
from .forms import ResidentLoginForm
from django.contrib.auth import views as auth_views 
from . import views 

app_name = 'resident_portal'

urlpatterns = [
    path('', views.public_home_view, name='public_home'), 
    
    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(
        template_name='resident_portal/login.html',
        authentication_form=ResidentLoginForm # <-- ITO ANG IDADAGDAG
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='resident_portal/logout.html'), name='logout'),

    # Protected Pages (Dashboard)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('blotter/create/', views.create_blotter_view, name='create_blotter'),
    path('report/create/', views.create_report_view, name='create_report'),
    path('my-schedules/', views.my_schedules_view, name='my_schedules'),
    path('about-us/', views.about_us_view, name='about_us'), 

    path('notifications/', views.notification_list_view, name='notification_list'),
    path('case/<int:pk>/', views.resident_case_detail_view, name='resident_case_detail'),

    path('announcements/', views.announcement_list_view, name='resident_announcement_list'),
    path('announcements/<int:pk>/', views.announcement_detail_view, name='resident_announcement_detail'),

    path('my-cases/', views.my_cases_hub_view, name='my_cases_hub'),
    path('my-cases/blotters/', views.my_blotters_list_view, name='my_blotters_list'),
    path('my-cases/reports/', views.my_reports_list_view, name='my_reports_list'),
    path('my-reports/summary/<int:pk>/', views.report_summary_view, name='report_summary'),
    path('my-reports/blotter-paper/<int:pk>/', views.blotter_paper_view, name='blotter_paper'),
    path('my-reports/hearing-schedule/<int:pk>/', views.hearing_schedule_view, name='hearing_schedule'),
    path('my-reports/general/<int:pk>/', views.resident_report_detail_view, name='resident_report_detail'),

    path('profile-settings/', views.profile_settings_view, name='profile_settings'),
    path('help-center/', views.resident_help_center_view, name='resident_help_center'),

    #path('verify/<uuid:token>/', views.verify_email_view, name='verify_email'),
    #path('activate/<str:uidb64>/<str:token>/', views.verify_email_view, name='verify_email'),
    #path('verify/<uuid:token>/', views.verify_email_view, name='verify_email'),

    path('password-reset/', views.request_password_reset_view, name='password_reset_request'),
    path('password-reset/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('password-reset/set-new/', views.set_new_password_view, name='set_new_password'),
    path('help-center/', views.help_center_view, name='help_center'),
    
]