#!/usr/bin/env bash
eval `ssh-agent -s`

/deploy/server_run.sh 2>&1 | tee /var/log/quipucords.log
