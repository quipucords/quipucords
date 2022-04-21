#!/usr/bin/env bash
eval `ssh-agent -s`

/deploy/server_run.sh 2>&1 | tee -a /var/log/quipucords.log
