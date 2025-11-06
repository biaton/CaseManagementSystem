from django.urls import path
from . import views

app_name = 'system_settings'

urlpatterns = [
    path('', views.settings_hub_view, name='hub'),
    
    # ==================================
    # Barangay Information URLs
    # ==================================
    path('edit-barangay-info/', views.edit_barangay_info_view, name='edit_barangay_info'),
    
    # ==================================
    # Hotlines CRUD URLs
    # ==================================
    path('manage-hotlines/', views.manage_hotlines_view, name='manage_hotlines'),
    path('hotlines/<int:pk>/edit/', views.edit_hotline_view, name='edit_hotline'),
    path('hotlines/<int:pk>/delete/', views.delete_hotline_view, name='delete_hotline'),

    # ==================================
    # Contacts CRUD URLs
    # ==================================
    path('manage-contacts/', views.manage_contacts_view, name='manage_contacts'),
    path('contacts/<int:pk>/edit/', views.edit_contact_view, name='edit_contact'),
    path('contacts/<int:pk>/delete/', views.delete_contact_view, name='delete_contact'),
    
    # ==================================
    # External Links CRUD URLs
    # ==================================
    path('manage-links/', views.manage_links_view, name='manage_links'),
    path('links/<int:pk>/edit/', views.edit_link_view, name='edit_link'),
    path('links/<int:pk>/delete/', views.delete_link_view, name='delete_link'),

    # ==================================
    # Officials Display CRUD URLs
    # ==================================
    path('manage-officials-display/', views.manage_officials_display_view, name='manage_officials_display'),
    path('officials-display/<int:pk>/edit/', views.edit_official_display_view, name='edit_official_display'),
    path('officials-display/<int:pk>/delete/', views.delete_official_display_view, name='delete_official_display'),

    path('manage-lupon-schedule/', views.manage_lupon_schedule_view, name='manage_lupon_schedule'),
    path('lupon/add/', views.add_lupon_member_view, name='add_lupon_member'),
    path('lupon/<int:pk>/edit/', views.edit_lupon_member_view, name='edit_lupon_member'),
    path('lupon/<int:pk>/delete/', views.delete_lupon_member_view, name='delete_lupon_member'),
]