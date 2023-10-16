"""Utilities for User management."""

from django.conf import settings
from django.contrib.auth.models import User


def create_random_password():
    """Create a random password for a User."""
    return User.objects.make_random_password(settings.QPC_MINIMUM_PASSWORD_LENGTH)
