"""
Context processors for adding tenant-specific data to all templates.
"""
from typing import Dict, Any
from django.http import HttpRequest
from django.core.cache import cache
from .models import SchoolSettings


def school_settings(request: HttpRequest) -> Dict[str, Any]:
    """
    Add school settings to the template context.
    Cached per tenant for better performance.
    """
    # Build cache key based on tenant schema
    from django.db import connection
    cache_key = f'school_settings_{connection.schema_name}'

    # Try to get from cache
    settings = cache.get(cache_key)

    if settings is None:
        # Get or create settings
        try:
            settings = SchoolSettings.get_settings()
            # Cache for 15 minutes
            cache.set(cache_key, settings, 900)
        except Exception:
            # Fallback if settings doesn't exist
            settings = None

    return {
        'school_settings': settings,
        'school_name': settings.short_name if settings else 'SmartSIS',
        'school_logo': settings.logo.url if settings and settings.logo else None,
        'school_motto': settings.motto if settings else '',
        'school_theme': settings.theme_name if settings else 'light',
    }
