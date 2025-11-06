from django.contrib import admin
from .models import Case # I-import natin ang Case model mula sa models.py

# Simple registration
admin.site.register(Case)