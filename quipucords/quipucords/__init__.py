"""quipucords Django project package with various configuration modules."""

from django.conf import settings

if settings.QPC_CELERY_ENABLE:
    from quipucords.celery import app as celery_app

    __all__ = ["celery_app"]
