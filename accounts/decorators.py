from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """
    Decorator to check if user has any of the required roles.
    Usage: @role_required('teacher', 'school_admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Check if user has any of the required roles
            has_role = any([
                user.is_superuser,
                user.is_school_admin and 'school_admin' in roles,
                user.is_teacher and 'teacher' in roles,
                user.is_student and 'student' in roles,
                user.is_parent and 'parent' in roles,
            ])
            
            if has_role:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard:home')
        
        return wrapper
    return decorator


def school_admin_required(view_func):
    """Decorator for school admin only views."""
    return role_required('school_admin')(view_func)


def teacher_required(view_func):
    """Decorator for teacher only views."""
    return role_required('teacher')(view_func)


def student_required(view_func):
    """Decorator for student only views."""
    return role_required('student')(view_func)


def parent_required(view_func):
    """Decorator for parent only views."""
    return role_required('parent')(view_func)