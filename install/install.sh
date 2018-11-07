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
RELEASE_TAG='-e RELEASE_TAG=0.0.46'
POSTGRES_VERSION='-e POSTGRES_VERSION=9.6.10'
#TODO: Uncomment CLI_PACKAGE_VERSION when cutting a release
#CLI_PACKAGE_VERSION="-e CLI_PACKAGE_VERSION=0.0.46-ACTUAL_COPR_GIT_COMMIT"



declare -a args
args=("$*")
#TODO: you will need to make sure that the package_version is in args
#args+=("$RELEASE_TAG" "$POSTGRES_VERSION" "$CLI_PACKAGE_VERSION")
args+=("$RELEASE_TAG" "$POSTGRES_VERSION")
set -- ${args[@]}

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
  echo "/etc/redhat-release not found. You need to run this on a Red Hat based OS."
  exit 1
fi

if dnf --version; then
  PKG_MGR=dnf
else
  PKG_MGR=yum
  if grep -q -i "release 7" /etc/redhat-release
  then
    RHEL7=1
  fi
fi

echo "Checking if ansible is installed..."
command -v ansible > /dev/null 2>&1

if [ $? -ne 0 ]
then
  echo "Ansible prerequisite could not be found. Trying to install ansible..."
  ansible_not_installed=1
fi

if [ $ansible_not_installed ]; then
  if [ $RHEL7 ]; then
    echo "Trying to install RHEL7 dependencies..."
    sudo subscription-manager repos --enable="rhel-7-server-extras-rpms" || true
    sudo subscription-manager repos --enable="rhel-7-server-optional-rpms" || true
  fi
  sudo "${PKG_MGR}" install -y ansible
fi

command -v ansible > /dev/null 2>&1

if [ $? -ne 0 ]
then
  echo ""
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
  exit 1
fi
