from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def dashboard(request):
    """
    The main dashboard controller.
    Renders the appropriate template based on the user's role.
    """
    user = request.user

    if user.is_superuser or user.is_school_admin:
        return _admin_dashboard(request)
    
    elif user.is_teacher:
        return _teacher_dashboard(request)
    
    elif user.is_student:
        return _student_dashboard(request)
    
    elif user.is_parent:
        return _parent_dashboard(request)
    
    else:
        # Fallback for users without a specific role
        return _generic_dashboard(request)


# --- Helper Functions (Internal) ---

def _admin_dashboard(request):
    """Admin/School Admin Dashboard"""
    from teachers.models import Teacher
    
    context = {
        'total_users': User.objects.count(),
        'teacher_count': Teacher.objects.filter(is_active=True).count(),
        'student_count': 0,  # TODO: Add when Student model exists
        'class_count': 0,     # TODO: Add when Class model exists
        'subject_count': 0,   # TODO: Add when Subject model exists
    }
    return render(request, 'dashboard/admin.html', context)


def _teacher_dashboard(request):
    """Teacher Dashboard"""
    context = {
        'my_classes': [],  # TODO: Fetch teacher's classes
        'recent_activity': [],
    }
    return render(request, 'dashboard/teacher.html', context)


def _student_dashboard(request):
    """Student Dashboard"""
    context = {
        'my_classes': [],  # TODO: Fetch student's classes
        'assignments': [],  # TODO: Fetch assignments
        'grades': [],       # TODO: Fetch grades
    }
    return render(request, 'dashboard/student.html', context)


def _parent_dashboard(request):
    """Parent Dashboard"""
    context = {
        'children': [],  # TODO: Fetch parent's children
        'recent_activity': [],
    }
    return render(request, 'dashboard/parent.html', context)


def _generic_dashboard(request):
    """Generic Dashboard for users without specific roles"""
    return render(request, 'dashboard/user.html')