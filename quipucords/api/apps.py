"""Apps module for Django server application."""

from django.apps import AppConfig
from django.conf import settings


class ApiConfig(AppConfig):
    """Defines the api application configuration."""

    name = "api"

    def ready(self):
        """Mark server ready."""
        settings.QUIPUCORDS_CACHED_REPORTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
