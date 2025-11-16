from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthenticationForm(AuthenticationForm):
    """Custom form for authenticating users with email."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use email as the username field
        self.fields['username'].label = 'Email'
        # Update widget classes to match new design
        self.fields['username'].widget.attrs.update(
            {'class': 'input input-bordered input-sm w-full', 'placeholder': 'your@email.com', 'required': True}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'input input-bordered input-sm w-full', 'placeholder': 'Enter password', 'required': True}
        )


class SignupForm(forms.ModelForm):
    """Custom form for user registration with email."""
    
    # Rename fields to match HTML name attributes
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create password', 
            'class': 'input input-bordered input-sm w-full',
            'required': True
        }),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password', 
            'class': 'input input-bordered input-sm w-full',
            'required': True
        }),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ('email',)
        widgets = {
            # Update widget classes
            'email': forms.EmailInput(attrs={
                'placeholder': 'your@email.com', 
                'class': 'input input-bordered input-sm w-full',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = "Email"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        """Validate that passwords match."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        """Save the new user."""
        user = super().save(commit=False)
        # Use password1 to set the password
        user.set_password(self.cleaned_data["password1"])
        
        # --- Set a default role for signup ---
        # For this example, we'll make them a student.
        # You can change this or add a role selector.
        user.is_student = True 
        
        if commit:
            user.save()
        return user