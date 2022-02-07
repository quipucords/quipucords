#!/usr/bin/env bash

source /opt/venv/bin/activate

make server-migrate server-set-superuser -C /app

if [[ ${USE_SUPERVISORD,,} = "false" ]]; then
    cd /app/quipucords
fi

/opt/venv/bin/gunicorn quipucords.wsgi -c /deploy/gunicorn.conf.py
