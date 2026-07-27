from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'user_type', 'is_vendor', 'date_joined')
    list_filter = ('user_type', 'is_vendor', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'profile_image', 'is_vendor')}),
    )
