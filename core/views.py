# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.core.cache import cache
from django.db import connection
from .models import SchoolSettings
from schools.models import School
from accounts.decorators import school_admin_required


def index_or_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Root URL handler for tenants.
    Redirects to dashboard if authenticated, login otherwise.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    else:
        return redirect('accounts:login')


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """User profile view - handled by accounts app"""
    return redirect('accounts:profile')


@login_required
@school_admin_required
def settings(request: HttpRequest) -> HttpResponse:
    """View and edit school settings (school admin only)."""
    settings_obj = SchoolSettings.get_settings()
    school = School.objects.get(schema_name=connection.schema_name)

    if request.method == 'POST':
        # Update settings (removed short_name as it comes from School model)
        settings_obj.motto = request.POST.get('motto', '')
        settings_obj.theme_name = request.POST.get('theme_name', settings_obj.theme_name)

        # Handle logo upload
        if 'logo' in request.FILES:
            settings_obj.logo = request.FILES['logo']

        settings_obj.save()

        # Clear cache
        cache_key = f'school_settings_{connection.schema_name}'
        cache.delete(cache_key)

        messages.success(request, 'Settings updated successfully!')
        return redirect('core:settings')

    return render(request, 'core/settings.html', {
        'settings': settings_obj,
        'school': school
    })


def logout_view(request: HttpRequest) -> HttpResponse:
    """Logout view"""
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')