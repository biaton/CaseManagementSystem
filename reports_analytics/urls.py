from django.urls import path
from . import views

app_name = 'reports_analytics'

urlpatterns = [
    path('', views.reports_hub_view, name='hub'),
    path('lupon-report/', views.lupon_report_view, name='lupon_report'),
    path('incident-type-report/', views.incident_type_report_view, name='incident_type_report'),
    path('monthly-analytics/', views.monthly_analytics_view, name='monthly_analytics'), 
]