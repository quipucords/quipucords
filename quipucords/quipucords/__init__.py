"""quipucords Django project package with various configuration modules."""

from quipucords.celery import app as celery_app

__all__ = ["celery_app"]
