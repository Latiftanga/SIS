from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def dashboard(request):
    """
    The main dashboard controller.
    Renders the appropriate template and context directly at the /dashboard/ URL
    based on the user's role, without redirecting.
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
# These are not views reachable by URL, but internal renderers.

def _admin_dashboard(request):
    context = {
        'total_users': User.objects.count(),
        'recent_activity': [], # Fetch admin specific data
    }
    return render(request, 'dashboard/admin.html', context)

def _teacher_dashboard(request):
    context = {
        'classes': [], # Fetch teacher specific data
    }
    return render(request, 'dashboard/teacher.html', context)

def _student_dashboard(request):
    context = {
        'assignments': [], # Fetch student specific data
    }
    return render(request, 'dashboard/student.html', context)

def _parent_dashboard(request):
    context = {
        'children': [], # Fetch parent specific data
    }
    return render(request, 'dashboard/parent.html', context)

def _generic_dashboard(request):
    return render(request, 'dashboard/user.html')