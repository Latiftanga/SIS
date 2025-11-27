from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomAuthenticationForm(AuthenticationForm):
    """Custom form for authenticating users with email."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs.update({
            'class': 'input input-bordered w-full',
            'placeholder': 'your@email.com',
            'required': True,
            'autofocus': True
        })
        self.fields['password'].widget.attrs.update({
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter password',
            'required': True
        })


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile (avatar only) - used by admins and non-teachers."""

    class Meta:
        model = User
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered file-input-sm w-full',
                'accept': 'image/*'
            }),
        }
        help_texts = {
            'avatar': 'Upload a profile picture (JPG, PNG)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].required = False


class TeacherProfileUpdateForm(forms.Form):
    """Form for teachers to update their profile - limited fields."""

    # User fields
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'file-input file-input-bordered file-input-sm w-full',
            'accept': 'image/*'
        }),
        help_text='Upload a profile picture (JPG, PNG)'
    )

    # Teacher fields
    other_names = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered input-sm w-full',
            'placeholder': 'Middle name or initials'
        }),
        help_text='Optional middle name or initials'
    )

    phone_number = forms.CharField(
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered input-sm w-full',
            'placeholder': '+233XXXXXXXXX or 0XXXXXXXXX'
        }),
        help_text='Phone number for contact'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Pre-populate fields if user has teacher profile
        if self.user and hasattr(self.user, 'teacher'):
            teacher = self.user.teacher
            self.fields['other_names'].initial = teacher.other_names
            self.fields['phone_number'].initial = teacher.phone_number

    def save(self):
        """Save both User and Teacher models."""
        if not self.user:
            return None

        # Update User avatar
        if self.cleaned_data.get('avatar'):
            self.user.avatar = self.cleaned_data['avatar']
            self.user.save()

        # Update Teacher fields
        if hasattr(self.user, 'teacher'):
            teacher = self.user.teacher
            teacher.other_names = self.cleaned_data.get('other_names', '')
            teacher.phone_number = self.cleaned_data['phone_number']
            teacher.save()

        return self.user