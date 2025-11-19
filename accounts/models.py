# accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom manager for User model with email-based authentication."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('Email address is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser (school admin)."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_school_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self._create_user(email, password, **extra_fields)

    def create_teacher(self, email, password=None, **extra_fields):
        """Create a teacher user."""
        extra_fields.setdefault('is_teacher', True)
        return self.create_user(email, password, **extra_fields)

    def create_student(self, email, password=None, **extra_fields):
        """Create a student user."""
        extra_fields.setdefault('is_student', True)
        return self.create_user(email, password, **extra_fields)

    def create_parent(self, email, password=None, **extra_fields):
        """Create a parent user."""
        extra_fields.setdefault('is_parent', True)
        return self.create_user(email, password, **extra_fields)

    def create_school_admin(self, email, password=None, **extra_fields):
        """Create a school admin user."""
        extra_fields.setdefault('is_school_admin', True)
        extra_fields.setdefault('is_staff', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email-based authentication and role management.
    Lives in EACH school's schema (tenant-specific).
    """

    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Role fields
    is_school_admin = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_parent = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Fix: Override groups and user_permissions with custom related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='school_user_set',
        related_query_name='school_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='school_user_set',
        related_query_name='school_user',
    )

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_teacher', 'is_active']),
            models.Index(fields=['is_student', 'is_active']),
            models.Index(fields=['is_parent', 'is_active']),
        ]

    def get_profile(self):
        """Return the related profile based on user role."""
        if self.is_student and hasattr(self, 'student'):
            return self.student
        elif self.is_teacher and hasattr(self, 'teacher'):
            return self.teacher
        elif self.is_parent and hasattr(self, 'parent'):
            return self.parent
        return None

    def get_full_name(self):
        """Return full name from related profile or fallback to email."""
        profile = self.get_profile()
        if profile and hasattr(profile, 'get_full_name'):
            return profile.get_full_name()
        return self.email.split('@')[0]

    def get_short_name(self):
        """Return short name from related profile or email username."""
        profile = self.get_profile()
        if profile and hasattr(profile, 'first_name'):
            return profile.first_name
        return self.email.split('@')[0]

    def get_user_type(self):
        """Return user type as string."""
        if self.is_superuser:
            return 'Super Admin'
        if self.is_school_admin:
            return 'School Admin'
        if self.is_teacher:
            return 'Teacher'
        if self.is_student:
            return 'Student'
        if self.is_parent:
            return 'Parent'
        return 'User'

    def has_role(self, role):
        """Check if user has a specific role."""
        role_map = {
            'school_admin': self.is_school_admin,
            'teacher': self.is_teacher,
            'student': self.is_student,
            'parent': self.is_parent,
            'staff': self.is_staff,
            'superuser': self.is_superuser,
        }
        return role_map.get(role.lower(), False)

    # Add profile picture field for the sidebar UI
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} ({self.email})" if full_name != self.email.split('@')[0] else self.email