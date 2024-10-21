"""Django signal handlers."""

from axes.signals import user_locked_out
from django.dispatch import receiver
from rest_framework.exceptions import PermissionDenied
from rest_framework.settings import api_settings as drf_settings

NON_FIELD_ERRORS_KEY = drf_settings.NON_FIELD_ERRORS_KEY


@receiver(user_locked_out)
def raise_permission_denied(*args, **kwargs):
    """Handle signal from Axes when user fails auth due to being locked out."""
    raise PermissionDenied(
        detail={NON_FIELD_ERRORS_KEY: ["Too many failed login attempts."]}
    )
