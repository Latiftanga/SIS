# schools/views.py
from django.shortcuts import render
from .models import School, Domain


def index(request):
    """
    Public landing page showing platform statistics.
    Only accessible from public schema via urls_public.py
    """
    # Get statistics
    total_schools = School.objects.count()
    active_schools = School.objects.filter(domains__isnull=False).distinct().count()
    
    # Get list of schools with their domains
    schools = School.objects.prefetch_related('domains').all()[:6]
    
    context = {
        'total_schools': total_schools,
        'active_schools': active_schools,
        'schools': schools,
    }
    
    return render(request, 'schools/index.html', context)