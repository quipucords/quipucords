#!/usr/bin/env python
"""Django server management module."""
import multiprocessing
import os
import sys

if __name__ == "__main__":
    if sys.platform == "darwin":
        multiprocessing.set_start_method("fork")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quipucords.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa: F401 pylint: disable=unused-import
        except ImportError as exception:
            raise ImportError(
                "Couldn't import Django. Are you sure it's "  # noqa: Q000
                "installed and available on your PYTHONPATH "  # noqa: Q000
                "environment variable? Did you "  # noqa: Q000
                "forget to activate a virtual environment?"  # noqa: Q000
            ) from exception
        raise
    execute_from_command_line(sys.argv)
