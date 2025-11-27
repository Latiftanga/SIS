from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


class Teacher(models.Model):
    """
    Teacher profile that can optionally be linked to a User account.
    Contains all teacher-specific information.
    """

    class Gender(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'

    # Optional link to User account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='teacher',
        null=True,
        blank=True,
        help_text='Optional user account for system access'
    )

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices)

    # Email for contact (independent of user account)
    email = models.EmailField(
        max_length=255,
        help_text='Teacher email address for communication'
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^(\+233|0)[2-5][0-9]{8}$',
        message="Phone must be: +233XXXXXXXXX or 0XXXXXXXXX"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17
    )
    
    # Employment Information
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique employee identification number'
    )
    date_joined = models.DateField(
        help_text='Date teacher joined the school'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'teacher'
        verbose_name_plural = 'teachers'

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self) -> str:
        """Return full name with other names if available"""
        if self.other_names:
            return f"{self.first_name} {self.other_names} {self.last_name}"
        return f"{self.first_name} {self.last_name}"