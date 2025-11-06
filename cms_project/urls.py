from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Resident Portal
    path('', include('resident_portal.urls')),

    # Official Portal URLs
    path('official/', include('official_portal.urls')),

    path('on-site/', include('onsite_reports.urls')),

    path('reports-analytics/', include('reports_analytics.urls')),

    path('settings/', include('system_settings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
