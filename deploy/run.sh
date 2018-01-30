#!/usr/bin/env bash

source ~/venv/bin/activate;~/venv/bin/gunicorn quipucords.wsgi -c /deploy/gunicorn.conf.py
