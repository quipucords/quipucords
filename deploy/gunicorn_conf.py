"""gunicorn configuration."""

import multiprocessing

import environ

from utils.debugger import start_debugger_if_required

env = environ.Env()

QPC_SERVER_PORT = env.int("QPC_SERVER_PORT", 8000)
QUIPUCORDS_HTTPS_ON = env.bool("QUIPUCORDS_HTTPS_ON", True)

bind = f"0.0.0.0:{QPC_SERVER_PORT}"
workers = multiprocessing.cpu_count() * 2 + 1

errorlog = "-"
loglevel = "info"
accesslog = "-"

# SSL configuration
if QUIPUCORDS_HTTPS_ON:
    keyfile = "/etc/ssl/qpc/server.key"
    certfile = "/etc/ssl/qpc/server.crt"

start_debugger_if_required()
