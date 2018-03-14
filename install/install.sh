#!/bin/bash

#
# Description: Install Quipucords server and command-line.
#

export PATH=$PATH:$ANSIBLE_HOME/bin
PLAYBOOKFILE="qpc_playbook.yml"

echo ansible-playbook $PLAYBOOKFILE $*
ansible-playbook $PLAYBOOKFILE -v -K $*

if [ $? -eq 0 ]
then
  echo "Installation complete."
else
  echo "Installation failed. Review the install logs."
  exit $?
fi
