#!/usr/bin/env bash
eval `ssh-agent -s`

/deploy/server_run.sh >& /var/log/quipucords.log
