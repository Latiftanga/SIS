from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from .forms import CustomAuthenticationForm, ProfileUpdateForm


def login_view(request):
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
            if request.htmx:
                response = HttpResponse()
                response['HX-Redirect'] = reverse('dashboard:index')
                return response
            
            return redirect('dashboard:index')
        else:
            # Invalid form - return form with errors
            if request.htmx:
                return render(request, 'accounts/partials/_login_form.html', {'form': form})
    
    else:  # GET request
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request):
    """Logs the user out."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def profile_view(request):
    """View user profile."""
    return render(request, 'accounts/profile.html')


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit(request):
    """Edit user profile with HTMX support."""
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            
            if request.htmx:
                # Return the updated profile view
                return render(request, 'accounts/partials/_profile_display.html')
            
            return redirect('profile')
        else:
            if request.htmx:
                return render(request, 'accounts/partials/_profile_edit_form.html', {'form': form})
    
    else:  # GET
        form = ProfileUpdateForm(instance=request.user)
    
    if request.htmx:
        return render(request, 'accounts/partials/_profile_edit_form.html', {'form': form})
    
    return render(request, 'accounts/profile_edit.html', {'form': form})