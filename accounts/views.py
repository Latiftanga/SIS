from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.http import HttpResponse
from .forms import CustomAuthenticationForm, SignupForm
from django.views.decorators.http import require_POST # <-- Import for logout

User = get_user_model()

def login_view(request):
    """Handles user login for the /login/ page."""
    
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            if request.htmx:
                response = HttpResponse()
                response['HX-Redirect'] = reverse(settings.LOGIN_REDIRECT_URL)
                return response
            
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            # POST is invalid. Check if HTMX.
            if request.htmx:
                # Return just the form fragment to swap
                return render(request, 'accounts/partials/_login_form.html', {'form': form})
            # If not HTMX, fall through to render the full page with errors
    
    else: # GET request
        form = CustomAuthenticationForm()

    # Full page render for GET requests or invalid non-HTMX POSTs
    return render(request, 'accounts/login.html', {'form': form})


def signup_view(request):
    """Handles user signup for the /signup/ page."""
    
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # <-- RE-ADDED: Auto-login the user
            
            # --- REDIRECT TO DASHBOARD ---
            redirect_url = reverse(settings.LOGIN_REDIRECT_URL) 

            if request.htmx:
                response = HttpResponse()
                response['HX-Redirect'] = redirect_url # Redirect to dashboard
                return response
            
            return redirect(redirect_url) # Redirect to dashboard
        else:
            # POST is invalid. Check if HTMX.
            if request.htmx:
                # Return just the form fragment to swap
                # Pass 'signup_form' as the context variable name
                return render(request, 'accounts/signup_form.html', {'signup_form': form})
            # If not HTMX, fall through to render the full page with errors
    
    else: # GET request
        form = SignupForm()

    # Full page render for GET requests or invalid non-HTMX POSTs
    # Pass 'signup_form' as the context variable name
    return render(request, 'accounts/signup.html', {'signup_form': form})


@require_POST # <-- ADDED: Make logout POST-only for security
def logout_view(request):
    """Logs the user out and redirects to the login page."""
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)