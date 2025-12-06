# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.core.cache import cache
from django.db import connection
from .models import SchoolSettings, AcademicYear, Term
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
        # Update settings
        settings_obj.motto = request.POST.get('motto', '')
        settings_obj.theme_name = request.POST.get('theme_name', settings_obj.theme_name)

        # Handle current term selection
        current_term_id = request.POST.get('current_term')
        if current_term_id:
            try:
                settings_obj.current_term = Term.objects.get(pk=current_term_id)
            except Term.DoesNotExist:
                settings_obj.current_term = None
        else:
            settings_obj.current_term = None

        # Handle academic year selection
        academic_year_id = request.POST.get('current_academic_year')
        if academic_year_id:
            try:
                settings_obj.current_academic_year = AcademicYear.objects.get(pk=academic_year_id)
            except AcademicYear.DoesNotExist:
                settings_obj.current_academic_year = None
        else:
            settings_obj.current_academic_year = None

        # Handle logo upload
        if 'logo' in request.FILES:
            settings_obj.logo = request.FILES['logo']

        settings_obj.save()

        # Clear cache
        cache_key = f'school_settings_{connection.schema_name}'
        cache.delete(cache_key)

        messages.success(request, 'Settings updated successfully!')
        return redirect('core:settings')

    # Get all academic years and terms for dropdown
    academic_years = AcademicYear.objects.all()
    terms = Term.objects.select_related('academic_year').order_by('-academic_year__start_date', 'number')

    return render(request, 'core/settings.html', {
        'settings': settings_obj,
        'school': school,
        'academic_years': academic_years,
        'terms': terms,
    })


@login_required
@school_admin_required
def academic_year_list(request: HttpRequest) -> HttpResponse:
    """List all academic years"""
    academic_years = AcademicYear.objects.all()
    return render(request, 'core/academic_years.html', {
        'academic_years': academic_years,
    })


@login_required
@school_admin_required
def academic_year_create(request: HttpRequest) -> HttpResponse:
    """Create a new academic year"""
    # Get redirect destination from query param or POST data
    next_url = request.POST.get('next') or request.GET.get('next', 'core:academic_years')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'

        if name and start_date and end_date:
            try:
                academic_year = AcademicYear.objects.create(
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=is_active
                )
                messages.success(request, f'Academic Year "{academic_year.name}" created successfully!')
                return redirect(next_url)
            except Exception as e:
                messages.error(request, f'Error creating academic year: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')

    return redirect(next_url)


@login_required
@school_admin_required
def academic_year_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit an academic year"""
    academic_year = get_object_or_404(AcademicYear, pk=pk)

    # Get redirect destination from query param or POST data
    next_url = request.POST.get('next') or request.GET.get('next', 'core:academic_years')

    if request.method == 'POST':
        academic_year.name = request.POST.get('name', '').strip()
        academic_year.start_date = request.POST.get('start_date')
        academic_year.end_date = request.POST.get('end_date')
        academic_year.is_active = request.POST.get('is_active') == 'on'

        try:
            academic_year.full_clean()
            academic_year.save()
            messages.success(request, f'Academic Year "{academic_year.name}" updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating academic year: {str(e)}')

    return redirect(next_url)


@login_required
@school_admin_required
def academic_year_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete an academic year"""
    academic_year = get_object_or_404(AcademicYear, pk=pk)

    # Get redirect destination from query param or POST data
    next_url = request.POST.get('next') or request.GET.get('next', 'core:academic_years')

    if request.method == 'POST':
        name = academic_year.name
        academic_year.delete()
        messages.success(request, f'Academic Year "{name}" deleted successfully!')

    return redirect(next_url)


# Term Management Views
@login_required
@school_admin_required
def term_create(request: HttpRequest) -> HttpResponse:
    """Create a new term/semester"""
    next_url = request.POST.get('next') or request.GET.get('next', 'core:settings')

    if request.method == 'POST':
        academic_year_id = request.POST.get('academic_year')
        name = request.POST.get('name', '').strip()
        number = request.POST.get('number')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_current = request.POST.get('is_current') == 'on'

        if academic_year_id and name and number and start_date and end_date:
            try:
                academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
                term = Term.objects.create(
                    academic_year=academic_year,
                    name=name,
                    number=number,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=is_current
                )
                messages.success(request, f'Term "{term.name}" created successfully!')
                return redirect(next_url)
            except Exception as e:
                messages.error(request, f'Error creating term: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')

    return redirect(next_url)


@login_required
@school_admin_required
def term_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a term/semester"""
    term = get_object_or_404(Term, pk=pk)
    next_url = request.POST.get('next') or request.GET.get('next', 'core:settings')

    if request.method == 'POST':
        term.name = request.POST.get('name', '').strip()
        term.number = request.POST.get('number')
        term.start_date = request.POST.get('start_date')
        term.end_date = request.POST.get('end_date')
        term.is_current = request.POST.get('is_current') == 'on'

        try:
            term.full_clean()
            term.save()
            messages.success(request, f'Term "{term.name}" updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating term: {str(e)}')

    return redirect(next_url)


@login_required
@school_admin_required
def term_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a term/semester"""
    term = get_object_or_404(Term, pk=pk)
    next_url = request.POST.get('next') or request.GET.get('next', 'core:settings')

    if request.method == 'POST':
        name = term.name
        term.delete()
        messages.success(request, f'Term "{name}" deleted successfully!')

    return redirect(next_url)


def logout_view(request: HttpRequest) -> HttpResponse:
    """Logout view"""
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')