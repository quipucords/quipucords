"""
WSGI config for quipucords project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quipucords.settings")

# pylint: disable=invalid-name
application = get_wsgi_application()

from scanner.manager import SCAN_MANAGER  # noqa: E402 pylint: disable=C0413

from . import environment  # noqa: E402 pylint: disable=C0413

environment.startup()
SCAN_MANAGER.start()
