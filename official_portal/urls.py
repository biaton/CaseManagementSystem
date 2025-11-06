from django.urls import path, reverse_lazy, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public-facing page for officials
    path('', views.official_home_view, name='official_home'),

    # Login page specific for officials
    path('login/', auth_views.LoginView.as_view(
        template_name='official_portal/login.html',
        next_page=reverse_lazy('official_dashboard') # Pagka-login, diretso sa official dashboard
    ), name='official_login'),

    path('logout/', views.custom_official_logout_view, name='official_logout'),

    # Protected dashboard
    path('dashboard/', views.official_dashboard_view, name='official_dashboard'),

    path('users/', views.manage_users_view, name='manage_users'),
    path('users/<int:pk>/profile/', views.resident_profile_view, name='resident_profile'),
    path('officials/<int:pk>/edit/', views.edit_official_view, name='edit_official'),
    path('users/<int:pk>/deactivate/', views.deactivate_user_view, name='deactivate_user'),
    path('notifications/', views.official_notification_list_view, name='official_notification_list'),

    path('users/approve/<int:pk>/', views.approve_resident_view, name='approve_resident'),

    path('records/', views.records_list_view, name='records_list'),
    path('records/<int:pk>/', views.record_detail_view, name='record_detail'),
    path('records/<int:pk>/proceedings/', views.manage_proceedings_view, name='manage_proceedings'),
    path('records/report/<int:pk>/', views.report_detail_view, name='report_detail'),
    path('reports/<int:pk>/quick-update/', views.quick_update_report_status_view, name='quick_update_report_status'),
    path('blotter/<int:pk>/delete/', views.delete_blotter_view, name='delete_blotter'),
    path('records/', views.records_list_view, name='list_records'),
    path('blotter/<int:pk>/notify-secretary/', views.notify_secretary_view, name='notify_secretary'),
    

    path('incident-logs/', views.incident_logs_view, name='incident_logs'),
    path('records/<int:case_pk>/settlement/', views.create_amicable_settlement_view, name='create_settlement'),

    path('announcements/', include('announcements.urls')),
    path('add-official/', views.add_official_view, name='add_official'),
    path('audit-trail/', views.audit_trail_view, name='audit_trail'),
    path('lupon-schedule/', views.lupon_schedule_view, name='lupon_schedule'),
    path('api/update-lupon-schedule/', views.update_lupon_schedule_api, name='api_update_lupon_schedule'),

    path('my-profile/', views.official_profile_view, name='official_profile'),
    path('change-password/', views.official_change_password_view, name='official_change_password'), 

    path('password-reset/', views.request_password_reset_official, name='official_password_reset_request'),
    path('password-reset/verify/', views.verify_otp_official, name='official_password_reset_verify'),
    path('password-reset/set-new/', views.set_new_password_official, name='official_password_reset_set_new'),
]