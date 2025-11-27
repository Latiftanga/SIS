# accounts/utils.py
"""Utility functions for account management."""
import secrets
import string
from typing import Tuple


def generate_secure_password(length: int = 8) -> str:
    """
    Generate a cryptographically secure random password.

    Best practices:
    - Uses secrets module (cryptographically secure)
    - Includes uppercase, lowercase, and digits
    - Ensures at least one of each character type
    - Default length of 8 characters (user-friendly)

    Args:
        length: Password length (minimum 8)

    Returns:
        str: A secure random password
    """
    if length < 8:
        length = 8  # Enforce minimum length

    # Define character sets - simplified for user-friendliness
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits

    # Ensure password has at least one of each character type
    password_chars = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
    ]

    # Fill the rest with random characters from all sets
    all_chars = uppercase + lowercase + digits
    password_chars += [secrets.choice(all_chars) for _ in range(length - 3)]

    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password_chars)

    return ''.join(password_chars)


def generate_username_from_email(email: str) -> str:
    """
    Extract username from email address.

    Args:
        email: Email address

    Returns:
        str: Username portion of email
    """
    return email.split('@')[0] if '@' in email else email


def format_password_for_display(password: str) -> Tuple[str, str]:
    """
    Format password for temporary display.
    Returns both full password and masked version.

    Args:
        password: The password to format

    Returns:
        Tuple[str, str]: (full_password, masked_password)
    """
    if len(password) <= 4:
        return password, '****'

    # Show first 2 and last 2 characters, mask the middle
    visible_chars = 2
    masked = (
        password[:visible_chars] +
        '*' * (len(password) - visible_chars * 2) +
        password[-visible_chars:]
    )

    return password, masked
