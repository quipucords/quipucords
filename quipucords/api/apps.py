"""Apps module for Django server application."""

from django.apps import AppConfig
from django.conf import settings


class ApiConfig(AppConfig):
    """Defines the api application configuration."""

    name = "api"

    def ready(self):
        """Mark server ready."""
        # We need to import any general signal handlers when the app becomes ready
        # because nothing else explicitly imports and loads them.
        from . import signals  # noqa: F401

        settings.QUIPUCORDS_CACHED_REPORTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
