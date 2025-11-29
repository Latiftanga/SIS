from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


class Programme(models.Model):
    """
    Academic programmes/tracks for SHS students (optional for Basic schools).
    Examples: Science, Business, Visual Arts, General Arts, Home Economics, etc.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Programme name (e.g., General Science, Business, Visual Arts)'
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Programme code (e.g., SCI, BUS, VART)'
    )
    description = models.TextField(
        blank=True,
        help_text='Programme description'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this programme is currently offered'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'programme'
        verbose_name_plural = 'programmes'

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Student(models.Model):
    """
    Student profile that can optionally be linked to a User account.
    Contains all student-specific information.
    """

    class Gender(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'

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

    # Optional link to User account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='student',
        null=True,
        blank=True,
        help_text='Optional user account for system access'
    )

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    
    # Contact Information
    email = models.EmailField(
        max_length=255,
        blank=True,
        help_text='Student email address for communication'
    )
    
    phone_regex = RegexValidator(
        regex=r'^(\+233|0)[2-5][0-9]{8}$',
        message="Phone must be: +233XXXXXXXXX or 0XXXXXXXXX"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text='Student contact number'
    )
    
    # Address
    residential_address = models.TextField(blank=True)
    
    # Student Information
    student_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique student identification number'
    )
    admission_date = models.DateField(
        help_text='Date student was admitted to the school'
    )
    current_grade = models.CharField(
        max_length=50,
        choices=GradeLevel.choices,
        help_text='Current grade/class'
    )
    
    # Guardian Information
    guardian_name = models.CharField(
        max_length=200,
        help_text='Full name of parent/guardian'
    )
    guardian_relationship = models.CharField(
        max_length=50,
        default='Parent',
        help_text='Relationship to student (Parent, Guardian, etc.)'
    )
    guardian_phone_regex = RegexValidator(
        regex=r'^(\+233|0)[2-5][0-9]{8}$',
        message="Phone must be: +233XXXXXXXXX or 0XXXXXXXXX"
    )
    guardian_phone = models.CharField(
        validators=[guardian_phone_regex],
        max_length=17,
        help_text='Guardian primary contact number'
    )
    guardian_email = models.EmailField(
        max_length=255,
        blank=True,
        help_text='Guardian email address'
    )
    guardian_address = models.TextField(
        blank=True,
        help_text='Guardian residential address'
    )
    
    # Emergency Contact (if different from guardian)
    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Emergency contact person'
    )
    emergency_contact_phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text='Emergency contact number'
    )
    
    # Medical Information
    medical_conditions = models.TextField(
        blank=True,
        help_text='Any medical conditions, allergies, or special needs'
    )
    
    # Photo
    photo = models.ImageField(
        upload_to='students/photos/',
        null=True,
        blank=True,
        help_text='Student photograph'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the student is currently enrolled'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['current_grade', 'last_name', 'first_name']
        verbose_name = 'student'
        verbose_name_plural = 'students'
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['current_grade', 'is_active']),
            models.Index(fields=['last_name', 'first_name']),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.student_id})"

    def get_full_name(self) -> str:
        """Return full name with other names if available"""
        if self.other_names:
            return f"{self.first_name} {self.other_names} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self) -> int:
        """Calculate student's age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
