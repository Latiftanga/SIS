from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


class Programme(models.Model):
    """
    Academic programmes/tracks for SHS students (optional for Basic schools).
    Examples: Science, Business, Visual Arts, General Arts, Home Economics, etc.

    Ghana SHS programmes have specific subject requirements:
    - Core Subjects: Mandatory for all students (English, Math, Integrated Science, Social Studies)
    - Required Electives: Must be taken by students in this programme
    - Optional Electives: Students choose based on availability

    Examples:
    - General Science: Must take Physics, Chemistry, Biology/Elective Science + Math
    - Business: Must take Business Management, Financial Accounting, Economics/Costing
    - Visual Arts: Must take Graphic Design, General Knowledge in Art, Picture Making
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
        help_text='Programme description and career paths'
    )

    # Subject Requirements for SHS Programmes
    core_subjects = models.ManyToManyField(
        'classes.Subject',
        related_name='core_for_programmes',
        blank=True,
        help_text='Core subjects required for all students in this programme '
                  '(e.g., English, Mathematics, Integrated Science, Social Studies)'
    )
    required_electives = models.ManyToManyField(
        'classes.Subject',
        related_name='required_for_programmes',
        blank=True,
        help_text='Required elective subjects for this programme '
                  '(e.g., Physics, Chemistry, Biology for Science programme)'
    )
    optional_electives_count = models.PositiveIntegerField(
        default=1,
        help_text='Number of optional elective subjects students must choose'
    )

    # Programme requirements
    minimum_aggregate = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Minimum BECE aggregate score required for admission (e.g., 6-30)'
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
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def get_total_required_subjects(self) -> int:
        """Get total number of required subjects (core + required electives)"""
        return self.core_subjects.count() + self.required_electives.count()

    def get_all_required_subjects(self):
        """Get all required subjects (core + required electives)"""
        from itertools import chain
        return list(chain(self.core_subjects.all(), self.required_electives.all()))


class Student(models.Model):
    """
    Student profile that can optionally be linked to a User account.
    Contains all student-specific information.
    """

    class Gender(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'

    class GuardianRelationship(models.TextChoices):
        PARENT = 'Parent', 'Parent'
        FATHER = 'Father', 'Father'
        MOTHER = 'Mother', 'Mother'
        GUARDIAN = 'Guardian', 'Guardian'
        GRANDMOTHER = 'Grandmother', 'Grandmother'
        GRANDFATHER = 'Grandfather', 'Grandfather'
        AUNT = 'Aunt', 'Aunt'
        UNCLE = 'Uncle', 'Uncle'
        SIBLING = 'Sibling', 'Sibling'
        OTHER = 'Other', 'Other'

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
    
    # Guardian Information
    guardian_name = models.CharField(
        max_length=200,
        help_text='Full name of parent/guardian'
    )
    guardian_relationship = models.CharField(
        max_length=50,
        choices=GuardianRelationship.choices,
        default=GuardianRelationship.PARENT,
        help_text='Relationship to student'
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

    # Boarding/Residence Status (for SHS students primarily)
    class ResidenceStatus(models.TextChoices):
        DAY = 'day', 'Day Student'
        BOARDING = 'boarding', 'Boarding Student'
        SEMI_BOARDING = 'semi_boarding', 'Semi-Boarding'

    residence_status = models.CharField(
        max_length=20,
        choices=ResidenceStatus.choices,
        blank=True,
        help_text='Residential status (applicable for SHS students)'
    )
    dormitory = models.CharField(
        max_length=100,
        blank=True,
        help_text='Dormitory or hostel name (for boarding students)'
    )
    bed_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Bed/cubicle number (for boarding students)'
    )

    # House Assignment (for house system)
    house = models.ForeignKey(
        'classes.House',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        help_text='House assignment for inter-house competitions'
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
        ordering = ['last_name', 'first_name']
        verbose_name = 'student'
        verbose_name_plural = 'students'
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['is_active']),
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

    def is_boarding_student(self) -> bool:
        """Check if student is a boarding student"""
        return self.residence_status == self.ResidenceStatus.BOARDING

    def is_day_student(self) -> bool:
        """Check if student is a day student"""
        return self.residence_status == self.ResidenceStatus.DAY

    def get_current_enrollment(self):
        """Get the student's current active enrollment"""
        return self.enrollments.filter(is_active=True).order_by('-created_at').first()

    def get_current_class(self):
        """Get the student's current class"""
        enrollment = self.get_current_enrollment()
        return enrollment.class_obj if enrollment else None

    def get_current_grade(self) -> str:
        """Get the student's current grade level from their class enrollment"""
        current_class = self.get_current_class()
        return current_class.grade_level if current_class else 'Not Enrolled'
