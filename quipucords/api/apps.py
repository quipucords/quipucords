"""Apps module for Django server application."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Defines the api application configuration."""

    name = "api"

    def ready(self):
        """Mark server ready."""
