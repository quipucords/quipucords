"""gunicorn configuration."""

import multiprocessing

import environ

from utils.debugger import start_debugger_if_required

env = environ.Env()

QUIPUCORDS_SERVER_PORT = env.int("QUIPUCORDS_SERVER_PORT", 8000)

bind = f"0.0.0.0:{QUIPUCORDS_SERVER_PORT}"
workers = multiprocessing.cpu_count() * 2 + 1

errorlog = "-"
loglevel = "info"
accesslog = "-"

start_debugger_if_required()
