from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML
from .forms import CustomAuthenticationForm, ProfileUpdateForm, TeacherProfileUpdateForm


def login_view(request: HttpRequest) -> HttpResponse:
    """Handles user login with HTMX support."""

    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            messages.success(request, f'Welcome back, {user.get_short_name()}!')

            # HTMX redirect
            if hasattr(request, 'htmx') and request.htmx:
                response = HttpResponse()
                response['HX-Redirect'] = reverse('dashboard:index')
                return response

            return redirect('dashboard:index')
        else:
            # Invalid form - return form with errors
            if hasattr(request, 'htmx') and request.htmx:
                return render(request, 'accounts/partials/_login_form.html', {'form': form})

    else:  # GET request
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    """Logs the user out."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """View user profile."""
    context = {
        'current_user': request.user
    }
    return render(request, 'accounts/profile.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit(request: HttpRequest) -> HttpResponse:
    """Edit user profile with HTMX support. Uses different forms based on user role."""

    # Determine which form to use based on user role
    is_teacher = request.user.is_teacher and hasattr(request.user, 'teacher')

    if request.method == 'POST':
        if is_teacher:
            # Teachers use TeacherProfileUpdateForm with limited editable fields
            form = TeacherProfileUpdateForm(request.POST, request.FILES, user=request.user)
        else:
            # Admins and others use basic ProfileUpdateForm (avatar only)
            form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')

            if hasattr(request, 'htmx') and request.htmx:
                # Trigger page reload to update avatar everywhere
                response = HttpResponse()
                response['HX-Redirect'] = '/profile/'
                return response

            return redirect('accounts:profile')
        else:
            if hasattr(request, 'htmx') and request.htmx:
                context = {
                    'form': form,
                    'is_teacher': is_teacher,
                    'current_user': request.user
                }
                return render(request, 'accounts/partials/_profile_edit_form.html', context)

    else:  # GET
        if is_teacher:
            form = TeacherProfileUpdateForm(user=request.user)
        else:
            form = ProfileUpdateForm(instance=request.user)

    context = {
        'form': form,
        'is_teacher': is_teacher,
        'current_user': request.user
    }

    if hasattr(request, 'htmx') and request.htmx:
        return render(request, 'accounts/partials/_profile_edit_form.html', context)

    return render(request, 'accounts/profile_edit.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request: HttpRequest) -> HttpResponse:
    """
    Force password change for users with auto-generated passwords.

    Best Practices:
    - Uses Django's built-in PasswordChangeForm for validation
    - Updates password_changed_at timestamp
    - Removes force_password_change flag
    - Keeps user logged in after password change
    - Shows clear instructions to the user
    """
    # Check if password change is required
    is_forced = getattr(request.user, 'force_password_change', False)

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()

            # Update password change tracking
            user.force_password_change = False
            user.password_changed_at = timezone.now()
            user.save()

            # Keep user logged in
            update_session_auth_hash(request, user)

            messages.success(
                request,
                'Your password has been changed successfully! You now have full access to the system.'
            )

            return redirect('dashboard:index')
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'form': form,
        'is_forced': is_forced,
    }

    return render(request, 'accounts/change_password.html', context)


@login_required
def profile_export_pdf(request: HttpRequest) -> HttpResponse:
    """
    Export user profile to PDF.
    Generates a professionally formatted PDF document with user information.
    """
    user = request.user
    profile = user.get_profile()

    # Prepare context for PDF template
    context = {
        'user': user,
        'profile': profile,
        'is_teacher': user.is_teacher and hasattr(user, 'teacher'),
        'is_student': user.is_student and hasattr(user, 'student'),
        'is_parent': user.is_parent and hasattr(user, 'parent'),
    }

    # Render HTML template
    html_string = render_to_string('accounts/profile_pdf.html', context)

    # Generate PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'profile_{user.email.split("@")[0]}_{timezone.now().strftime("%Y%m%d")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response