from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


class Teacher(models.Model):
    """
    Teacher profile linked to User via OneToOneField.
    Contains all teacher-specific information.
    """
    # Link to User account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher'
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    
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

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        """Return full name with other names if available"""
        if self.other_names:
            return f"{self.first_name} {self.other_names} {self.last_name}"
        return f"{self.first_name} {self.last_name}"