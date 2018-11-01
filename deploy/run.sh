#!/usr/bin/env bash
eval `ssh-agent -s`
source ~/venv/bin/activate;make server-migrate server-set-superuser -C /app;~/venv/bin/gunicorn quipucords.wsgi -c /deploy/gunicorn.conf.py
