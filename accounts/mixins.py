from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to check if user has required role(s)."""
    
    required_roles = []  # List of required roles
    
    def test_func(self):
        """Check if user has any of the required roles."""
        user = self.request.user
        
        if user.is_superuser:
            return True
        
        return any([
            user.is_school_admin and 'school_admin' in self.required_roles,
            user.is_teacher and 'teacher' in self.required_roles,
            user.is_student and 'student' in self.required_roles,
            user.is_parent and 'parent' in self.required_roles,
        ])
    
    def handle_no_permission(self):
        """Redirect with error message if user doesn't have permission."""
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('dashboard:home')


class SchoolAdminRequiredMixin(RoleRequiredMixin):
    """Mixin for school admin only views."""
    required_roles = ['school_admin']


class TeacherRequiredMixin(RoleRequiredMixin):
    """Mixin for teacher only views."""
    required_roles = ['teacher']


class StudentRequiredMixin(RoleRequiredMixin):
    """Mixin for student only views."""
    required_roles = ['student']


class ParentRequiredMixin(RoleRequiredMixin):
    """Mixin for parent only views."""
    required_roles = ['parent']