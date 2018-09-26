#!/bin/bash
#===============================================================================
#
#          FILE:  install.sh
#
#         USAGE:  ./install.sh
#
#   DESCRIPTION:  Install Quipucords server and command-line components.
#
#       OPTIONS:  -h | --help   Obtain command USAGE
#                 -e | --extra-vars  set additional variables as key=value
#===============================================================================

export PATH=$PATH:$ANSIBLE_HOME/bin
PLAYBOOKFILE="qpc_playbook.yml"


usage() {
    cat <<EOM
    Install Quipucords server and command-line components.

    Usage:
    $(basename $0)

    Options:
    -h | --help   Obtain command USAGE
    -e | --extra-vars  set additional variables as key=value


    Extra Variables:
    * Specify fully-qualified directory path for local install packages (defaults to `pwd`/packages/):
         -e pkg_install_dir=/home/user/pkgs
    * Skipping install for server:
         -e install_server=false
    * Skipping install for CLI:
         -e install_cli=false
    * Specify server port (defaults to 443):
         -e server_port=8443
    * Specify server container name (defaults to quipucords):
         -e server_name=qpc_server
    * Optionally specify the postgres db user (if not specified the default value is 'postgres'):
         -e QPC_DBMS_USER=postgres
    * Optionally specify the postgres db password (if not specified the default value is 'password')
         -e QPC_DBMS_PASSWORD=password
    * Override default server timeout for HTTP requests (if not specified the default value is 120):
         -e QPC_SERVER_TIMEOUT=120
EOM
    exit 0
}

if [[ ($1 == "--help") ||  ($1 == "-h") ]]
then
  usage;
fi

if [ ! -f /etc/redhat-release ]; then
  echo '/etc/redhat-release not found. You need to run this on a Red Hat based OS.'
  exit 1
fi

if dnf --version; then
  PKG_MGR=dnf
else
  PKG_MGR=yum
fi

echo 'Checking if ansible is installed...'
command -v ansible > /dev/null 2>&1

if [ $? -ne 0 ]
then
  echo 'Ansible prerequisite could not be found. Trying to install ansible...'
  ansible_not_installed=1
fi

if [ $ansible_not_installed ]; then
  sudo "${PKG_MGR}" install -y ansible
fi

command -v ansible > /dev/null 2>&1

if [ $? -ne 0 ]
then
  echo "Installation failed. Ansible prerequisite could not be installed."
  echo "Follow installation documentation for installing Ansible."
  exit 1
fi

if [[ $EUID -ne 0 ]]
then
  echo ansible-playbook $PLAYBOOKFILE -v -K $*
  ansible-playbook $PLAYBOOKFILE -v -K $*
else
  echo ansible-playbook $PLAYBOOKFILE -v $*
  ansible-playbook $PLAYBOOKFILE -v $*
fi

if [ $? -eq 0 ]
then
  echo "Installation complete."
else
  echo "Installation failed. Review the install logs."
  exit $?
fi
