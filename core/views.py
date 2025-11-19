# core/views.py
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages


def index_or_dashboard(request):
    """
    Root URL handler for tenants.
    Redirects to dashboard if authenticated, login otherwise.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')  # Redirect to dashboard app
    else:
        return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile view - handled by accounts app"""
    return redirect('profile')


@login_required
def settings(request):
    """Settings view - placeholder for now"""
    from django.shortcuts import render
    return render(request, 'core/settings.html')


def logout_view(request):
    """Logout view"""
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')