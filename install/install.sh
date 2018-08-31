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
    * Specify postgresql as database management system (default is to use SQLite):
         -e use_postgres=false
    * Specify postgresql db name:
         -e QPC_DBMS_DATABASE=postgres
    * Specify postgresql db user:
         -e QPC_DBMS_USER=postgres
    * Specify postgresql db password:
         -e QPC_DBMS_PASSWORD=None
    * Specify postgresql db host:
         -e QPC_DBMS_HOST=None
    * Specify postgresql db port:
         -e QPC_DBMS_PORT=5432
EOM
    exit 0
}

if [[ ($1 == "--help") ||  ($1 == "-h") ]]
then
  usage;
fi

command -v ansible > /dev/null 2>&1

if [ $? -ne 0 ]
then
  echo "Installation failed. Ansible prerequisite could not be found."
  echo "Follow installation documentation for installing Ansible."
  exit 1
fi


echo ansible-playbook $PLAYBOOKFILE -v -K $*
ansible-playbook $PLAYBOOKFILE -v -K $*

if [ $? -eq 0 ]
then
  echo "Installation complete."
else
  echo "Installation failed. Review the install logs."
  exit $?
fi
