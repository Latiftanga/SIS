from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from teachers.models import Teacher
from students.models import Student


class Subject(models.Model):
    """
    Represents a subject taught in the school (e.g., Mathematics, English, Science).
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Subject name (e.g., Mathematics, English)'
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Subject code (e.g., MATH101, ENG101)'
    )
    description = models.TextField(
        blank=True,
        help_text='Subject description'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this subject is currently offered'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'subject'
        verbose_name_plural = 'subjects'

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Class(models.Model):
    """
    Represents a class/grade in the school (e.g., Grade 1A, JHS 2B).
    A class is a group of students in the same grade/level.
    Name is auto-generated from grade_level + section.
    """

    class GradeLevel(models.TextChoices):
        # Early Childhood
        NURSERY = 'Nursery', 'Nursery'
        KG1 = 'KG 1', 'KG 1'
        KG2 = 'KG 2', 'KG 2'
        # Primary School (Basic 1-6)
        PRIMARY_1 = 'Primary 1', 'Primary 1'
        PRIMARY_2 = 'Primary 2', 'Primary 2'
        PRIMARY_3 = 'Primary 3', 'Primary 3'
        PRIMARY_4 = 'Primary 4', 'Primary 4'
        PRIMARY_5 = 'Primary 5', 'Primary 5'
        PRIMARY_6 = 'Primary 6', 'Primary 6'
        # Junior High School (Basic 7-9)
        JHS_1 = 'JHS 1', 'JHS 1'
        JHS_2 = 'JHS 2', 'JHS 2'
        JHS_3 = 'JHS 3', 'JHS 3'
        # Senior High School
        SHS_1 = 'SHS 1', 'SHS 1'
        SHS_2 = 'SHS 2', 'SHS 2'
        SHS_3 = 'SHS 3', 'SHS 3'

    name = models.CharField(
        max_length=100,
        editable=False,
        help_text='Auto-generated from grade level and section'
    )
    grade_level = models.CharField(
        max_length=50,
        choices=GradeLevel.choices,
        help_text='Select grade/level'
    )
    section = models.CharField(
        max_length=10,
        blank=True,
        help_text='Section/stream (e.g., A, B, C, Science, Arts)'
    )
    
    # Class teacher (homeroom teacher)
    class_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homeroom_classes',
        help_text='Class teacher/Form master'
    )

    # Programme (for SHS classes only - optional)
    programme = models.ForeignKey(
        'students.Programme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes',
        help_text='Academic programme (for SHS classes only - e.g., Science, Business, Visual Arts)'
    )

    # Capacity
    capacity = models.PositiveIntegerField(
        default=40,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        help_text='Maximum number of students'
    )
    
    # Academic year
    academic_year = models.CharField(
        max_length=20,
        help_text='Academic year (e.g., 2024/2025)'
    )
    
    # Room information
    room_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Classroom number/location'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this class is currently active'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['grade_level', 'section', 'name']
        verbose_name = 'class'
        verbose_name_plural = 'classes'
        unique_together = [['grade_level', 'section', 'academic_year']]
        indexes = [
            models.Index(fields=['grade_level', 'is_active']),
            models.Index(fields=['academic_year', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        """Auto-generate class name from grade_level and section"""
        if self.section:
            self.name = f"{self.grade_level} {self.section}"
        else:
            self.name = self.grade_level
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
    
    def get_student_count(self) -> int:
        """Get the number of enrolled students"""
        return self.enrollments.filter(is_active=True).count()
    
    def get_available_capacity(self) -> int:
        """Get remaining capacity"""
        return self.capacity - self.get_student_count()
    
    def is_full(self) -> bool:
        """Check if class is at capacity"""
        return self.get_student_count() >= self.capacity


class ClassSubject(models.Model):
    """
    Links subjects to classes with assigned teachers.
    Represents which subjects are taught in which classes and by whom.
    """
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_subjects',
        verbose_name='Class'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='class_assignments'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subject_assignments',
        help_text='Teacher assigned to teach this subject in this class'
    )
    
    # Schedule information (optional - can be expanded to full timetable later)
    periods_per_week = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text='Number of periods per week'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this subject is currently being taught'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['class_obj', 'subject']
        ordering = ['class_obj', 'subject']
        verbose_name = 'class subject'
        verbose_name_plural = 'class subjects'

    def __str__(self) -> str:
        teacher_name = self.teacher.get_full_name() if self.teacher else 'No teacher'
        return f"{self.class_obj.name} - {self.subject.name} ({teacher_name})"


class StudentEnrollment(models.Model):
    """
    Tracks student enrollment in classes.
    Maintains complete historical record of student's academic journey.
    Each enrollment represents one academic year in one class.
    """

    class EnrollmentStatus(models.TextChoices):
        ENROLLED = 'enrolled', 'Currently Enrolled'
        COMPLETED = 'completed', 'Completed'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        TRANSFERRED = 'transferred', 'Transferred Out'

    class FinalResult(models.TextChoices):
        PROMOTED = 'promoted', 'Promoted to Next Grade'
        REPEATED = 'repeated', 'Repeated Grade'
        GRADUATED = 'graduated', 'Graduated'
        TRANSFERRED = 'transferred', 'Transferred'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        PENDING = 'pending', 'Pending (Year Not Complete)'

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Class'
    )

    # Academic year tracking
    academic_year = models.CharField(
        max_length=20,
        default='2024/2025',  # Default for migration, should be set explicitly
        help_text='Academic year for this enrollment (e.g., 2024/2025)',
        db_index=True
    )

    # Enrollment dates
    enrollment_date = models.DateField(
        help_text='Date student was enrolled in this class'
    )
    completion_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date student completed/left this class'
    )

    # Roll number (position in class)
    roll_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Student roll number in this class'
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ENROLLED,
        help_text='Current status of this enrollment'
    )

    final_result = models.CharField(
        max_length=20,
        choices=FinalResult.choices,
        default=FinalResult.PENDING,
        blank=True,
        help_text='Final outcome of this enrollment'
    )

    # Active flag (True only for current academic year)
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this is the current enrollment (current academic year only)',
        db_index=True
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this enrollment'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-academic_year', '-enrollment_date', 'roll_number']
        verbose_name = 'student enrollment'
        verbose_name_plural = 'student enrollments'
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['class_obj', 'is_active']),
            models.Index(fields=['academic_year', 'is_active']),
            models.Index(fields=['student', 'academic_year']),
        ]
        unique_together = [['student', 'academic_year']]  # One enrollment per student per year

    def __str__(self) -> str:
        return f"{self.student.get_full_name()} in {self.class_obj.name} ({self.academic_year})"

    def complete_enrollment(self, completion_date, final_result):
        """Mark enrollment as completed with final result"""
        self.completion_date = completion_date
        self.final_result = final_result
        self.status = self.EnrollmentStatus.COMPLETED
        self.is_active = False
        self.save()

    def is_current_year(self) -> bool:
        """Check if this is the current academic year enrollment"""
        return self.is_active and self.status == self.EnrollmentStatus.ENROLLED
