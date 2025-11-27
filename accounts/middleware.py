# accounts/middleware.py
"""Middleware for account security and management."""
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.http import HttpRequest, HttpResponse
from typing import Callable


class ForcePasswordChangeMiddleware:
    """
    Middleware to force users to change their password on first login.

    Implements security best practice:
    - Users created with auto-generated passwords must change them
    - Prevents access to other pages until password is changed
    - Allows access to logout and password change pages
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Check if user is authenticated and needs to change password
        if not request.user.is_authenticated:
            return self.get_response(request)

        if not hasattr(request.user, 'force_password_change'):
            return self.get_response(request)

        if not request.user.force_password_change:
            return self.get_response(request)

        # User needs to change password - check if they're on an allowed page
        current_path = request.path

        # Allow static and media files
        if current_path.startswith('/static/') or current_path.startswith('/media/'):
            return self.get_response(request)

        # Allow access to change password page (check multiple patterns)
        if ('/change-password' in current_path or
            '/password-change' in current_path or
            current_path.endswith('/change-password/') or
            current_path.endswith('/password-change/')):
            return self.get_response(request)

        # Allow logout
        if '/logout' in current_path:
            return self.get_response(request)

        # Get the current view name safely
        try:
            resolved = resolve(request.path)
            if resolved.url_name in ['change_password', 'login', 'logout']:
                return self.get_response(request)
        except:
            pass

        # Redirect to password change page
        return redirect('accounts:change_password')
