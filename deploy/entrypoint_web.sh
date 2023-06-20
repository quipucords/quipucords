#!/usr/bin/env bash

if [[ "${QPC_ENABLE_CELERY_SCAN_MANAGER:-0}" == "0" ]]; then
    # ssh-agent is required for thread-based scan manager
    eval `ssh-agent -s`
    GUNICORN_CONF="/deploy/legacy_gunicorn_conf.py"
else
    # our gunicorn config is a relic from the past - gunicorn standards are good enough
    # 1. with this simpler config we delegate to nginx to deal with https shenanigans
    # 2. we can set a higher number of workers, since there's no risk for race conditions
    #    with the celery-based manager
    GUNICORN_CONF="/deploy/gunicorn_conf.py"
fi

make server-migrate server-set-superuser -C /app
gunicorn quipucords.wsgi -c $GUNICORN_CONF
