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
        'name', 'grade_level', 'get_school_level', 'section', 'programme',
        'class_teacher', 'capacity', 'academic_year', 'is_active'
    ]
    list_filter = ['is_active', 'grade_level', 'academic_year', 'programme']
    search_fields = ['name', 'grade_level', 'section', 'room_number']
    readonly_fields = ['name', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('grade_level', 'section', 'academic_year'),
            'description': 'Name will be auto-generated from grade level and section'
        }),
        ('SHS Programme (For SHS Classes Only)', {
            'fields': ('programme',),
            'description': 'Only applicable to Senior High School (SHS 1-3) classes'
        }),
        ('Teacher & Capacity', {
            'fields': ('class_teacher', 'capacity', 'room_number')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('name', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_school_level(self, obj):
        """Display the school level (Early Childhood, Primary, JHS, SHS)"""
        return obj.get_school_level()
    get_school_level.short_description = 'School Level'
    get_school_level.admin_order_field = 'grade_level'


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
        'student', 'class_obj', 'academic_year', 'enrollment_date',
        'status', 'final_result', 'roll_number', 'is_active'
    ]
    list_filter = [
        'is_active', 'status', 'final_result', 'academic_year',
        'class_obj__grade_level', 'enrollment_date'
    ]
    search_fields = [
        'student__first_name', 'student__last_name',
        'student__student_id', 'class_obj__name', 'academic_year'
    ]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Student & Class', {
            'fields': ('student', 'class_obj', 'academic_year')
        }),
        ('Enrollment Period', {
            'fields': ('enrollment_date', 'completion_date')
        }),
        ('Status & Results', {
            'fields': ('status', 'final_result', 'is_active'),
            'description': 'Track student progression through Ghana\'s education system'
        }),
        ('Class Details', {
            'fields': ('roll_number',)
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
