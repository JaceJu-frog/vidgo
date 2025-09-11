from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    
    # Fields to display in the admin list
    list_display = ('username', 'email', 'premium_authority', 'is_staff', 'is_active', 'created_at')
    list_filter = ('premium_authority', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email')
    
    # Add premium_authority and hidden_categories to the fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Premium Features', {
            'fields': ('premium_authority', 'hidden_categories'),
        }),
    )
    
    # Fields for creating a new user
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Premium Features', {
            'fields': ('premium_authority', 'hidden_categories'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
