"""Celery configuration for quipucords."""

import os

import environ
from celery import Celery, signals

from quipucords.environment import start_debugger_if_required

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quipucords.settings")

env = environ.Env()
app = Celery("quipucords")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
task_packages = ["scanner", "scanner.satellite.five", "scanner.satellite.six"]
app.autodiscover_tasks(task_packages)
start_debugger_if_required()

if env.bool("QPC_DISABLE_CELERY_LOGGING_HIJACK", True):

    @signals.setup_logging.connect
    def on_celery_setup_logging(**kwargs):
        """
        Stop Celery from overriding default logging setup.

        By default, celery hijacks the root logger. The configuration setting
        CELERY_WORKER_HIJACK_ROOT_LOGGER only stops Celery from updating the handler;
        celery still updates the formatter, and we can lose filters.

        Since the formatter we want to use is the configured Django one,
        we can just configure Celery not to touch logging.
        """
