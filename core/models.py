from __future__ import annotations
from django.db import models


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
