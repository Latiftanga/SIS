from __future__ import annotations
from django.db import models
from django.core.exceptions import ValidationError


class AcademicYear(models.Model):
    """
    Academic year definition for the school.
    Used by classes, attendance, grading, and other academic operations.
    """
    class PeriodSystem(models.TextChoices):
        TERMS = 'terms', '3 Terms (Basic Schools)'
        SEMESTERS = 'semesters', '2 Semesters (SHS)'

    name = models.CharField(
        max_length=20,
        unique=True,
        help_text='Academic year name (e.g., "2024/2025")'
    )
    start_date = models.DateField(help_text='Start date of the academic year')
    end_date = models.DateField(help_text='End date of the academic year')
    period_system = models.CharField(
        max_length=10,
        choices=PeriodSystem.choices,
        default=PeriodSystem.TERMS,
        help_text='Whether to use 3 terms (Basic schools) or 2 semesters (SHS)'
    )
    is_active = models.BooleanField(
        default=False,
        help_text='Set as the current active academic year'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'

    def __str__(self) -> str:
        return self.name

    def clean(self):
        """Validate that end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValidationError({
                'end_date': 'End date must be after start date'
            })

    def get_number_of_periods(self) -> int:
        """Get the number of periods based on period system"""
        return 3 if self.period_system == self.PeriodSystem.TERMS else 2

    def get_period_name(self, number: int) -> str:
        """Get the display name for a period number"""
        if self.period_system == self.PeriodSystem.TERMS:
            return f"Term {number}"
        else:
            return f"Semester {number}"

    def save(self, *args, **kwargs):
        """Ensure only one active academic year and create terms/semesters"""
        is_new = self.pk is None
        if self.is_active:
            # Deactivate all other academic years
            AcademicYear.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

        # Auto-create terms/semesters for new academic years
        if is_new:
            self.create_periods()

    def create_periods(self):
        """Create terms or semesters based on period_system"""
        from datetime import timedelta

        num_periods = self.get_number_of_periods()
        total_days = (self.end_date - self.start_date).days
        days_per_period = total_days // num_periods

        for i in range(1, num_periods + 1):
            # Calculate period dates
            if i == 1:
                period_start = self.start_date
            else:
                period_start = self.start_date + timedelta(days=days_per_period * (i - 1))

            if i == num_periods:
                period_end = self.end_date
            else:
                period_end = self.start_date + timedelta(days=days_per_period * i - 1)

            Term.objects.get_or_create(
                academic_year=self,
                number=i,
                defaults={
                    'name': self.get_period_name(i),
                    'start_date': period_start,
                    'end_date': period_end,
                }
            )


class Term(models.Model):
    """
    Represents a term or semester within an academic year.
    Automatically created based on the academic year's period system.
    - Basic schools: 3 terms per year
    - SHS: 2 semesters per year
    """
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='terms',
        help_text='Academic year this term belongs to'
    )
    name = models.CharField(
        max_length=20,
        help_text='Term/Semester name (e.g., "Term 1", "Semester 2")'
    )
    number = models.PositiveSmallIntegerField(
        help_text='Term/Semester number (1, 2, or 3)'
    )
    start_date = models.DateField(help_text='Start date of this term/semester')
    end_date = models.DateField(help_text='End date of this term/semester')
    is_current = models.BooleanField(
        default=False,
        help_text='Whether this is the currently active term/semester'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['academic_year', 'number']
        unique_together = [['academic_year', 'number']]
        verbose_name = 'Term/Semester'
        verbose_name_plural = 'Terms/Semesters'
        indexes = [
            models.Index(fields=['academic_year', 'number']),
            models.Index(fields=['is_current']),
        ]

    def __str__(self) -> str:
        return f"{self.academic_year.name} - {self.name}"

    def clean(self):
        """Validate that end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValidationError({
                'end_date': 'End date must be after start date'
            })

    def save(self, *args, **kwargs):
        """Ensure only one term is current at a time"""
        if self.is_current:
            # Deactivate all other terms
            Term.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class SchoolSettings(models.Model):
    """
    School-specific settings and branding for each tenant.
    Each tenant has ONE instance of this model.
    """
    # Branding
    short_name = models.CharField(
        max_length=20,
        default='SmartSIS',
        help_text='Short name displayed in navbar'
    )
    motto = models.CharField(
        max_length=100,
        blank=True,
        help_text='School motto or tagline'
    )
    logo = models.ImageField(
        upload_to='school_logos/',
        blank=True,
        null=True,
        help_text='School logo'
    )

    # Theme
    theme_name = models.CharField(
        max_length=50,
        default='light',
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('cupcake', 'Cupcake'),
            ('emerald', 'Emerald'),
            ('corporate', 'Corporate'),
            ('forest', 'Forest'),
            ('luxury', 'Luxury'),
        ],
        help_text='DaisyUI theme'
    )

    # Academic Session
    current_academic_year = models.ForeignKey(
        'AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='settings_using',
        help_text='Current active academic year'
    )
    current_term = models.ForeignKey(
        'Term',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='settings_using',
        help_text='Current active term/semester'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'School Settings'
        verbose_name_plural = 'School Settings'

    def __str__(self) -> str:
        return f"{self.short_name} Settings"

    def save(self, *args, **kwargs):
        """Ensure only one instance exists per tenant"""
        if not self.pk and SchoolSettings.objects.exists():
            raise ValueError('Only one SchoolSettings instance allowed per school')
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls) -> 'SchoolSettings':
        """Get or create the single settings instance for this tenant"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
