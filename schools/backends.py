from django.contrib.auth.backends import ModelBackend
from django.db import connection
from schools.models import PlatformUser
from accounts.models import User


class TenantAwareBackend(ModelBackend):
    """
    Custom authentication backend that handles both:
    1. Platform users (public schema) - for platform admin
    2. School users (tenant schemas) - for school admin
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user based on current schema
        """
        if username is None:
            username = kwargs.get('email')  # Support email field
        
        current_schema = connection.schema_name
        
        # Public schema - authenticate platform users
        if current_schema == 'public':
            try:
                user = PlatformUser.objects.get(email=username)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except PlatformUser.DoesNotExist:
                # Run the default password hasher once to reduce timing
                # difference between existing and non-existing users
                PlatformUser().set_password(password)
                return None
        
        # Tenant schema - authenticate school users
        else:
            try:
                user = User.objects.get(email=username)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except User.DoesNotExist:
                # Run the default password hasher once to reduce timing
                User().set_password(password)
                return None
        
        return None
    
    def get_user(self, user_id):
        """
        Retrieve user based on current schema
        """
        current_schema = connection.schema_name
        
        # Public schema - get platform user
        if current_schema == 'public':
            try:
                user = PlatformUser.objects.get(pk=user_id)
                return user if self.user_can_authenticate(user) else None
            except PlatformUser.DoesNotExist:
                return None
        
        # Tenant schema - get school user
        else:
            try:
                user = User.objects.get(pk=user_id)
                return user if self.user_can_authenticate(user) else None
            except User.DoesNotExist:
                return None


class PlatformBackend(ModelBackend):
    """
    Backend specifically for platform users (public schema only).
    Use this if you want separate authentication for platform admin.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Only authenticate against PlatformUser model"""
        if username is None:
            username = kwargs.get('email')
        
        # Only work in public schema
        if connection.schema_name != 'public':
            return None
        
        try:
            user = PlatformUser.objects.get(email=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except PlatformUser.DoesNotExist:
            PlatformUser().set_password(password)
            return None
        
        return None
    
    def get_user(self, user_id):
        """Get PlatformUser by ID"""
        if connection.schema_name != 'public':
            return None
        
        try:
            user = PlatformUser.objects.get(pk=user_id)
            return user if self.user_can_authenticate(user) else None
        except PlatformUser.DoesNotExist:
            return None


class SchoolBackend(ModelBackend):
    """
    Backend specifically for school users (tenant schemas only).
    Use this if you want separate authentication for school admin.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Only authenticate against User model"""
        if username is None:
            username = kwargs.get('email')
        
        # Don't work in public schema
        if connection.schema_name == 'public':
            return None
        
        try:
            user = User.objects.get(email=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            User().set_password(password)
            return None
        
        return None
    
    def get_user(self, user_id):
        """Get User by ID"""
        if connection.schema_name == 'public':
            return None
        
        try:
            user = User.objects.get(pk=user_id)
            return user if self.user_can_authenticate(user) else None
        except User.DoesNotExist:
            return None