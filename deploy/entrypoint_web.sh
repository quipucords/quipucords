#!/usr/bin/env bash
eval `ssh-agent -s`

make server-migrate server-set-superuser -C /app | tee -a /var/log/quipucords.log
gunicorn quipucords.wsgi -c /deploy/gunicorn.conf.py | tee -a /var/log/quipucords.log
