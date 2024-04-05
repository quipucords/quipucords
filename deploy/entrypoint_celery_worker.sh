#!/usr/bin/env bash
# shellcheck disable=SC2312
eval "$(ssh-agent -s)"

make celery-worker 2>&1 | tee -a /var/log/celery_worker.log
