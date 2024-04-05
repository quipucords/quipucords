#!/usr/bin/env bash

set -e

handle_certificates() {
    # verify if user provided certificates exist or create a self signed certificate.
    CERTS_PATH="/etc/ssl/qpc"
    mkdir -p "${CERTS_PATH}"
    if [[ -f "${CERTS_PATH}/server.key" ]] && [[ -f "${CERTS_PATH}/server.crt" ]]; then
        echo "Using user provided certificates..."
        openssl rsa -in "${CERTS_PATH}/server.key" -check
        openssl x509 -in "${CERTS_PATH}/server.crt" -text -noout
    elif [[ ! -f "${CERTS_PATH}/server.key" ]] && [[ ! -f "${CERTS_PATH}/server.crt" ]]; then
        echo "No certificates provided. Creating them..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "${CERTS_PATH}/server.key" \
            -out "${CERTS_PATH}/server.crt" \
            -subj "/C=US/ST=Raleigh/L=Raleigh/O=IT/OU=IT Department/CN=example.com"
    else
        echo "Either key or certificate is missing."
        echo "Please provide both named as server.key and server.crt."
        echo "Tip: this container expects these files at ${CERTS_PATH}/"
        exit 1
    fi
}

if [[ "${QPC_ENABLE_CELERY_SCAN_MANAGER:-0}" == "0" ]]; then
    # ssh-agent is required for thread-based scan manager
    # shellcheck disable=SC2312
    eval "$(ssh-agent -s)"
    # handling certificates is only required for our legacy gunicorn configuration.
    # in the future discovery won't require any of this and a nginx proxy will
    # handle this (DISCOVERY-522)
    handle_certificates
    GUNICORN_CONF="/deploy/legacy_gunicorn_conf.py"
else
    # our gunicorn config is a relic from the past - gunicorn standards are good enough
    # 1. with this simpler config we delegate to nginx to deal with https shenanigans
    # 2. we can set a higher number of workers, since there's no risk for race conditions
    #    with the celery-based manager
    handle_certificates
    GUNICORN_CONF="/deploy/gunicorn_conf.py"
fi

# We only start the server if both the DB
# migration succeeds and the superuser is created.
if make server-migrate server-set-superuser -C /app; then
    gunicorn quipucords.wsgi -c "${GUNICORN_CONF}"
fi
