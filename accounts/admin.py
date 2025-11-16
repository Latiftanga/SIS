from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Define admin model for custom User model."""

    # Use email and password for creation
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password'),
        }),
    )
    
    # Fields to display in the change form
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ()}),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
        }),
        # Add role flags here
        ('Roles', {
            'fields': (
                'is_school_admin', 'is_teacher', 'is_student', 'is_parent'
            ),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to display in the list view
    list_display = (
        'email',
        'get_user_type',
        'is_active',
        'is_staff',
        'is_superuser',
    )
    
    list_filter = (
        'is_active', 
        'is_staff', 
        'is_superuser', 
        'is_school_admin', 
        'is_teacher', 
        'is_student', 
        'is_parent'
    )
    
    search_fields = ('email',)
    ordering = ('email',)
    
    # Required for custom user model
    filter_horizontal = ('groups', 'user_permissions',)
    
    # Hide the original username field
    exclude = ('username',)