#!/usr/bin/env bash

make server-migrate server-set-superuser -C /app

gunicorn quipucords.wsgi -c /deploy/gunicorn.conf.py
