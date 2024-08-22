"""
WSGI config for quipucords project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quipucords.settings")

application = get_wsgi_application()

from . import environment  # noqa: E402

environment.startup()

from scanner import manager  # noqa: E402

if not manager.SCAN_MANAGER:
    manager.reinitialize()
