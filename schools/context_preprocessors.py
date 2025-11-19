# schools/context_processors.py
def school_context(request):
    """
    Add school settings to all templates.
    """
    school = None
    school_settings = None
    
    # Get current tenant
    if hasattr(request, 'tenant') and request.tenant.schema_name != 'public':
        school = request.tenant
        
        # Get or create school settings
        from settings.models import SchoolSettings
        school_settings, created = SchoolSettings.objects.get_or_create(
            defaults={
                'short_name': school.name[:20],  # Use tenant name as default
            }
        )
    
    return {
        'school': school,
        'school_settings': school_settings,
        'current_user': request.user if request.user.is_authenticated else None,
    }