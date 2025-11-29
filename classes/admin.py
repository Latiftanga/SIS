from django.contrib import admin
from .models import Subject, Class, ClassSubject, StudentEnrollment


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Subject Information', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'grade_level', 'section', 'class_teacher',
        'capacity', 'academic_year', 'is_active'
    ]
    list_filter = ['is_active', 'grade_level', 'academic_year']
    search_fields = ['name', 'grade_level', 'section', 'room_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Class Information', {
            'fields': ('name', 'grade_level', 'section', 'academic_year')
        }),
        ('Teacher & Capacity', {
            'fields': ('class_teacher', 'capacity', 'room_number')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = [
        'class_obj', 'subject', 'teacher', 'periods_per_week', 'is_active'
    ]
    list_filter = ['is_active', 'class_obj', 'subject']
    search_fields = ['class_obj__name', 'subject__name', 'teacher__first_name', 'teacher__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('class_obj', 'subject', 'teacher')
        }),
        ('Schedule', {
            'fields': ('periods_per_week', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'class_obj', 'enrollment_date', 
        'roll_number', 'is_active'
    ]
    list_filter = ['is_active', 'class_obj', 'enrollment_date']
    search_fields = [
        'student__first_name', 'student__last_name', 
        'student__student_id', 'class_obj__name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Enrollment Details', {
            'fields': ('student', 'class_obj', 'enrollment_date', 'completion_date')
        }),
        ('Class Information', {
            'fields': ('roll_number', 'is_active')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
