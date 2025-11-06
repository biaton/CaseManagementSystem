from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Ito ang mga columns na makikita sa listahan ng users
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active',)
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name',)
    ordering = ('email',)

    # --- ITO ANG MGA MAHALAGANG PAGBABAGO ---

    # Para sa EDIT page ng user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'middle_name', 'suffix', 'gender', 'birthday', 'address', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Para sa ADD page ng user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'),
        }),
    )
    
    # Hindi na natin kailangan ang model = CustomUser dahil automatic na ito kapag ni-register

# Irehistro na natin ang CustomUser gamit ang custom admin settings
admin.site.register(CustomUser, CustomUserAdmin)