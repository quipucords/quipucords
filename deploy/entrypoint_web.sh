#!/usr/bin/env bash

set -e
shopt -s inherit_errexit

GUNICORN_CONF="/deploy/gunicorn_conf.py"

SCRIPT_PATH=$(realpath "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(dirname "${SCRIPT_PATH}")
"${SCRIPT_DIR}"/check_related_services_liveness.sh

# We only start the server if both the DB
# migration succeeds and the superuser is created.
if make server-migrate server-set-superuser -C /app; then
    gunicorn quipucords.wsgi -c "${GUNICORN_CONF}"
fi
