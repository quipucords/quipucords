#!/usr/bin/env bash
# shellcheck disable=SC2312
eval "$(ssh-agent -s)"

SCRIPT_PATH=$(realpath "${BASH_SOURCE[0]}")
SCRIPT_DIR=$(dirname "${SCRIPT_PATH}")
"${SCRIPT_DIR}"/check_related_services_liveness.sh

make celery-worker 2>&1 | tee -a /var/log/celery_worker.log
