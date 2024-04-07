#!/usr/bin/env bash

set -e
shopt -s inherit_errexit

function check_svc_status() {
    local SVC_HOST=$1 SVC_PORT=$2
    [[ $# -lt 2 ]] && echo "Error: Usage: check_svc_status SVC_HOST SVC_PORT" && exit 1

    while true; do
        echo "Checking ${SVC_HOST}:${SVC_PORT} status..."
        ncat "${SVC_HOST}" "${SVC_PORT}" </dev/null && break
        sleep 5
    done
    echo "${SVC_HOST}:${SVC_PORT} is accepting connections"
}

function get_django_config() {
    local CONFIG_NAME=$1
    [[ $# -lt 1 ]] && echo "Error: Usage: get_django_config CONFIG_NAME" && exit 1

    PYTHON=$(poetry run command -v python 2>/dev/null || command -v python)
    echo "from django.conf import settings;print(settings.${CONFIG_NAME})" |
        "${PYTHON}" quipucords/manage.py shell --settings quipucords.settings
}

function check_db_liveness() {
    local QPC_DBMS
    QPC_DBMS=$(get_django_config QPC_DBMS)
    if [[ "${QPC_DBMS}" == "postgres" ]]; then
        local PSQL_HOST
        PSQL_HOST=$(get_django_config "DATABASES['default']['HOST']")
        local PSQL_PORT
        PSQL_PORT=$(get_django_config "DATABASES['default']['PORT']")
        check_svc_status "${PSQL_HOST}" "${PSQL_PORT}"
    else
        echo "Skipping postgres liveness check."
    fi
}

check_db_liveness
