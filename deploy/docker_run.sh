#!/usr/bin/env bash
eval `ssh-agent -s`

if [[ ${USE_SUPERVISORD,,} = "false" ]]; then
    echo "Running without supervisord"
    /deploy/server_run.sh >& /var/log/quipucords.log
else
    echo "Running with supervisord"
    /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
fi
