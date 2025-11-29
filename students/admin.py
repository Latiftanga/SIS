from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'student_id',
        'first_name',
        'last_name',
        'current_grade',
        'admission_date',
        'is_active'
    ]
    list_filter = ['is_active', 'current_grade', 'gender', 'admission_date']
    search_fields = ['first_name', 'last_name', 'student_id', 'guardian_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'other_names', 'date_of_birth', 'gender', 'photo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'residential_address')
        }),
        ('Student Information', {
            'fields': ('student_id', 'admission_date', 'current_grade', 'is_active')
        }),
        ('Guardian Information', {
            'fields': (
                'guardian_name', 'guardian_relationship', 'guardian_phone',
                'guardian_email', 'guardian_address'
            )
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        ('Medical Information', {
            'fields': ('medical_conditions',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
