from typing import Optional, Any
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest
from django.db import connection
from schools.models import PlatformUser
from accounts.models import User


class TenantAwareBackend(ModelBackend):
    """
    Custom authentication backend that handles both:
    1. Platform users (public schema) - for platform admin
    2. School users (tenant schemas) - for school admin
    """

    def authenticate(
        self,
        request: Optional[HttpRequest],
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any
    ) -> Optional[User | PlatformUser]:
        """
        Authenticate user based on current schema
        """
        if username is None:
            username = kwargs.get('email')  # Support email field

        if username is None or password is None:
            return None

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

    def get_user(self, user_id: int) -> Optional[User | PlatformUser]:
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

    def authenticate(
        self,
        request: Optional[HttpRequest],
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any
    ) -> Optional[PlatformUser]:
        """Only authenticate against PlatformUser model"""
        if username is None:
            username = kwargs.get('email')

        if username is None or password is None:
            return None

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

    def get_user(self, user_id: int) -> Optional[PlatformUser]:
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

    def authenticate(
        self,
        request: Optional[HttpRequest],
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any
    ) -> Optional[User]:
        """Only authenticate against User model"""
        if username is None:
            username = kwargs.get('email')

        if username is None or password is None:
            return None

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

    def get_user(self, user_id: int) -> Optional[User]:
        """Get User by ID"""
        if connection.schema_name == 'public':
            return None

        try:
            user = User.objects.get(pk=user_id)
            return user if self.user_can_authenticate(user) else None
        except User.DoesNotExist:
            return None