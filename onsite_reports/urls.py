from django.urls import path
from . import views

app_name = 'onsite_reports' # Ito ay para sa namespacing (e.g., onsite_reports:hub)

urlpatterns = [
    path('', views.reporting_hub_view, name='hub'),
    path('create-blotter/', views.create_onsite_blotter_view, name='create_blotter'),
    path('create-report/', views.create_onsite_report_view, name='create_report'),
    path('blotters/', views.view_onsite_blotters_view, name='view_blotters'), 
    path('reports/', views.view_onsite_reports_view, name='view_reports'),
    
]