#!/usr/bin/env bash

source ~/venv/bin/activate

make server-migrate -C /app

python --version

cat /app/deploy/setup_user.py | python /app/quipucords/manage.py shell --settings quipucords.settings -v 3

if [[ ${USE_SUPERVISORD,,} = "false" ]]; then
    cd /app/quipucords
fi

~/venv/bin/gunicorn quipucords.wsgi -c /deploy/gunicorn.conf.py
