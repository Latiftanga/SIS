from django.db import models
from django.utils import timezone
from classes.models import Class, ClassSubject, StudentEnrollment
from students.models import Student
from teachers.models import Teacher


class AttendanceSession(models.Model):
    """
    Represents a specific attendance-taking session.
    Can be daily (whole day) or subject-specific (for a particular period).
    """

    class SessionType(models.TextChoices):
        DAILY = 'daily', 'Daily Attendance'
        SUBJECT = 'subject', 'Subject/Period Attendance'

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='attendance_sessions'
    )
    academic_year = models.ForeignKey(
        'core.AcademicYear',
        on_delete=models.PROTECT,
        related_name='attendance_sessions',
        null=True,
        blank=True,
        help_text='Academic year for this attendance session'
    )
    date = models.DateField(default=timezone.now)
    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
        default=SessionType.DAILY
    )
    subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Required for subject-specific attendance'
    )
    period_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='Period number for subject attendance (1-8)'
    )
    marked_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_finalized = models.BooleanField(
        default=False,
        help_text='Once finalized, attendance cannot be changed'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = [['class_obj', 'date', 'session_type', 'subject', 'period_number']]
        indexes = [
            models.Index(fields=['class_obj', 'date']),
            models.Index(fields=['date', 'session_type']),
            models.Index(fields=['academic_year', 'date']),
        ]

    def __str__(self):
        if self.session_type == self.SessionType.DAILY:
            return f"{self.class_obj.name} - {self.date} (Daily)"
        return f"{self.class_obj.name} - {self.subject.subject.name} - {self.date}"

    def get_present_count(self):
        """Count of students marked present"""
        return self.records.filter(status=AttendanceRecord.Status.PRESENT).count()

    def get_absent_count(self):
        """Count of students marked absent"""
        return self.records.filter(status=AttendanceRecord.Status.ABSENT).count()

    def get_late_count(self):
        """Count of students marked late"""
        return self.records.filter(status=AttendanceRecord.Status.LATE).count()

    def get_total_students(self):
        """Total number of enrolled students"""
        return self.records.count()

    def get_attendance_percentage(self):
        """Calculate attendance percentage"""
        total = self.get_total_students()
        if total == 0:
            return 0
        present_and_late = self.get_present_count() + self.get_late_count()
        return round((present_and_late / total) * 100, 2)


class AttendanceRecord(models.Model):
    """
    Individual student attendance record for a specific session.
    """

    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'
        LATE = 'late', 'Late'
        EXCUSED = 'excused', 'Excused Absence'

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text='The enrollment this attendance is tied to'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT
    )
    time_in = models.TimeField(
        null=True,
        blank=True,
        help_text='Time of arrival for late students'
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student__last_name', 'student__first_name']
        unique_together = [['session', 'student']]
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['enrollment', 'status']),
        ]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.session.date} - {self.get_status_display()}"
