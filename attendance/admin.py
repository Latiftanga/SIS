from django.contrib import admin
from .models import AttendanceSession, AttendanceRecord


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['class_obj', 'date', 'session_type', 'subject', 'get_attendance_percentage', 'is_finalized']
    list_filter = ['session_type', 'is_finalized', 'date', 'class_obj']
    search_fields = ['class_obj__name', 'notes']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status', 'time_in']
    list_filter = ['status', 'session__date', 'session__class_obj']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_id']
    readonly_fields = ['created_at', 'updated_at']
