# schools/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import School
import re


class SchoolCreationForm(forms.ModelForm):
    """
    Simple form for creating a school with its first admin user.
    """
    # School admin user fields
    admin_email = forms.EmailField(
        label='School Admin Email',
        widget=forms.EmailInput(attrs={'placeholder': 'admin@school.com'})
    )
    admin_password = forms.CharField(
        label='Admin Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Min. 8 characters'})
    )
    admin_password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'})
    )
    
    # Domain field
    domain = forms.CharField(
        label='Domain',
        widget=forms.TextInput(attrs={'placeholder': 'amass.localhost or schoolname'})
    )

    class Meta:
        model = School
        fields = ['name', 'schema_name']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'T. I. Ahmadiyya SHS',
            }),
            'schema_name': forms.TextInput(attrs={
                'placeholder': 'ti_ahmadiyya (lowercase, letters, numbers, underscores)',
            }),
        }

    def clean_schema_name(self):
        """Validate schema name"""
        schema_name = self.cleaned_data.get('schema_name', '').strip().lower()
        
        if not schema_name:
            raise ValidationError('Schema name is required.')
        
        # Must start with a letter and contain only letters, numbers, underscores
        if not re.match(r'^[a-z][a-z0-9_]*$', schema_name):
            raise ValidationError(
                'Schema name must start with a letter and contain only lowercase letters, numbers, and underscores.'
            )
        
        if len(schema_name) < 2:
            raise ValidationError('Schema name must be at least 2 characters.')
        
        if len(schema_name) > 63:
            raise ValidationError('Schema name too long (max 63 characters).')
        
        # Reserved names
        reserved = ['public', 'postgres', 'admin', 'template0', 'template1']
        if schema_name in reserved or schema_name.startswith('pg_'):
            raise ValidationError(f'"{schema_name}" is reserved.')
        
        # Check if exists
        if School.objects.filter(schema_name=schema_name).exists():
            raise ValidationError(f'Schema "{schema_name}" already exists.')
        
        return schema_name

    def clean_domain(self):
        """Validate domain"""
        domain = self.cleaned_data.get('domain', '').strip().lower()
        
        if not domain:
            raise ValidationError('Domain is required.')
        
        # Basic validation - allow letters, numbers, dots, hyphens
        if not re.match(r'^[a-z0-9.-]+$', domain):
            raise ValidationError('Domain can only contain letters, numbers, dots, and hyphens.')
        
        if len(domain) > 253:
            raise ValidationError('Domain too long.')
        
        # Check if exists
        from .models import Domain
        if Domain.objects.filter(domain__iexact=domain).exists():
            raise ValidationError(f'Domain "{domain}" already in use.')
        
        return domain

    def clean_admin_email(self):
        """Validate email"""
        email = self.cleaned_data.get('admin_email', '').strip().lower()
        
        if not email:
            raise ValidationError('Email is required.')
        
        validate_email(email)
        return email

    def clean(self):
        """Validate passwords match"""
        cleaned_data = super().clean()
        password = cleaned_data.get('admin_password')
        password_confirm = cleaned_data.get('admin_password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('admin_password_confirm', 'Passwords do not match.')
            
            if len(password) < 8:
                self.add_error('admin_password', 'Password must be at least 8 characters.')

        return cleaned_data


class SchoolChangeForm(forms.ModelForm):
    """Form for editing schools"""
    
    class Meta:
        model = School
        fields = ['name']