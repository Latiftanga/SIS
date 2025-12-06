from django.contrib import admin
from django.utils.html import format_html
from .models import (
    GradingPeriod, AssessmentType, SubjectAssessment,
    StudentGrade, GradingScale, TermGrade,
    ConductGrade, ReportCard
)


@admin.register(GradingPeriod)
class GradingPeriodAdmin(admin.ModelAdmin):
    list_display = [
        'term', 'start_date', 'end_date',
        'grade_entry_deadline', 'is_current_display', 'is_active'
    ]
    list_filter = ['term__academic_year', 'is_current', 'is_active']
    search_fields = ['term__name', 'term__academic_year__name']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Period Information', {
            'fields': ('term', 'is_current', 'is_active')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'grade_entry_deadline', 'report_generation_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_current_display(self, obj):
        if obj.is_current:
            return format_html('<span style="color: green;">✓ Current</span>')
        return ''
    is_current_display.short_description = 'Current'


@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_exam', 'default_weight', 'default_max_score', 'is_active']
    list_filter = ['is_exam', 'is_active']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']


@admin.register(SubjectAssessment)
class SubjectAssessmentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'class_subject', 'grading_period',
        'assessment_type', 'max_score', 'weight',
        'date_conducted', 'is_published'
    ]
    list_filter = [
        'grading_period', 'assessment_type',
        'is_published', 'date_conducted'
    ]
    search_fields = ['name', 'class_subject__subject__name', 'class_subject__class_obj__name']
    date_hierarchy = 'date_conducted'
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['class_subject', 'created_by']

    fieldsets = (
        ('Assessment Details', {
            'fields': ('name', 'class_subject', 'grading_period', 'assessment_type')
        }),
        ('Scoring', {
            'fields': ('max_score', 'weight', 'date_conducted')
        }),
        ('Additional Info', {
            'fields': ('description', 'is_published', 'created_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'assessment', 'score', 'percentage_display',
        'is_excused', 'graded_by', 'graded_at'
    ]
    list_filter = [
        'assessment__grading_period',
        'assessment__class_subject',
        'is_excused'
    ]
    search_fields = [
        'student__first_name', 'student__last_name',
        'student__student_id', 'assessment__name'
    ]
    readonly_fields = ['graded_at', 'created_at', 'updated_at', 'percentage_display', 'weighted_score_display']
    autocomplete_fields = ['student', 'assessment', 'enrollment', 'graded_by']

    fieldsets = (
        ('Grade Information', {
            'fields': ('assessment', 'student', 'enrollment')
        }),
        ('Score', {
            'fields': ('score', 'is_excused', 'percentage_display', 'weighted_score_display')
        }),
        ('Comments & Grading Info', {
            'fields': ('remarks', 'graded_by', 'graded_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def percentage_display(self, obj):
        percentage = obj.get_percentage()
        if percentage is not None:
            return f"{percentage:.2f}%"
        return "—"
    percentage_display.short_description = 'Percentage'

    def weighted_score_display(self, obj):
        weighted = obj.get_weighted_score()
        if weighted is not None:
            return f"{weighted:.2f}"
        return "—"
    weighted_score_display.short_description = 'Weighted Score'


@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    list_display = [
        'grade', 'min_score', 'max_score',
        'interpretation', 'grade_point', 'is_passing'
    ]
    list_filter = ['is_passing']
    search_fields = ['grade', 'interpretation']
    ordering = ['-min_score']


@admin.register(TermGrade)
class TermGradeAdmin(admin.ModelAdmin):
    list_display = [
        'student_name', 'subject', 'grading_period',
        'continuous_assessment_score', 'exam_score',
        'total_score', 'grade', 'class_position'
    ]
    list_filter = [
        'grading_period', 'class_subject__subject',
        'grade'
    ]
    search_fields = [
        'enrollment__student__first_name',
        'enrollment__student__last_name',
        'class_subject__subject__name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['enrollment', 'class_subject']

    def student_name(self, obj):
        return obj.enrollment.student.get_full_name()
    student_name.short_description = 'Student'

    def subject(self, obj):
        return obj.class_subject.subject.name
    subject.short_description = 'Subject'


@admin.register(ConductGrade)
class ConductGradeAdmin(admin.ModelAdmin):
    list_display = [
        'student_name', 'grading_period', 'conduct_area',
        'rating', 'rating_display'
    ]
    list_filter = ['grading_period', 'conduct_area', 'rating']
    search_fields = [
        'enrollment__student__first_name',
        'enrollment__student__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['enrollment']

    def student_name(self, obj):
        return obj.enrollment.student.get_full_name()
    student_name.short_description = 'Student'

    def rating_display(self, obj):
        return obj.get_rating_display()
    rating_display.short_description = 'Rating Level'


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = [
        'student_name', 'grading_period', 'average_score',
        'gpa', 'class_position', 'attendance_percentage',
        'is_published'
    ]
    list_filter = [
        'grading_period', 'is_published'
    ]
    search_fields = [
        'enrollment__student__first_name',
        'enrollment__student__last_name',
        'enrollment__student__student_id'
    ]
    readonly_fields = ['generated_at', 'updated_at']
    autocomplete_fields = ['enrollment', 'promoted_to']

    fieldsets = (
        ('Student & Period', {
            'fields': ('enrollment', 'grading_period')
        }),
        ('Academic Performance', {
            'fields': (
                'total_score', 'average_score', 'gpa',
                'class_position', 'total_students'
            )
        }),
        ('Attendance', {
            'fields': (
                'days_present', 'days_absent',
                'days_school_opened', 'attendance_percentage'
            )
        }),
        ('Comments', {
            'fields': ('class_teacher_comment', 'head_teacher_comment')
        }),
        ('Promotion', {
            'fields': ('promoted_to', 'is_published')
        }),
        ('Metadata', {
            'fields': ('generated_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def student_name(self, obj):
        return obj.enrollment.student.get_full_name()
    student_name.short_description = 'Student'
