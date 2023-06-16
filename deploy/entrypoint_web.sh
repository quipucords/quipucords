#!/usr/bin/env bash
eval `ssh-agent -s`

if [[ "${QPC_ENABLE_CELERY_SCAN_MANAGER:-0}" == "0" ]]; then
    make server-migrate server-set-superuser -C /app | tee -a /var/log/quipucords.log
    gunicorn quipucords.wsgi -c /deploy/gunicorn.conf.py | tee -a /var/log/quipucords.log
else
    # Would be better to have a init-container doing the migration
    make server-migrate server-set-superuser -C /app
    # our gunicorn config is a relic from the past - gunicorn standards are good enough
    # 1. with this simpler config we delegate to nginx to deal with https shenanigans
    # 2. we can set a higher number of workers, since there's no risk for race conditions
    #    with the thread-based manager
    # NOTE: when QPC_DEBUGPY is enabled, set QPC_WEB_PARALLEL_WORKERS to 1
    gunicorn quipucords.wsgi -w ${QPC_WEB_PARALLEL_WORKERS:-1} -b :${QPC_SERVER_PORT:-8000}
fi
