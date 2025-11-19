from django.contrib import admin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id',
        'first_name', 
        'last_name',
        'phone_number',
        'date_joined',
        'is_active'
    ]
    list_filter = ['is_active', 'date_joined']
    search_fields = ['first_name', 'last_name', 'employee_id', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'gender', 'date_of_birth' 'other_names', 'phone_number')
        }),
        ('Employment Information', {
            'fields': ('employee_id', 'date_joined', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )