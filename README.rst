.. image:: https://travis-ci.org/quipucords/quipucords.svg?branch=master
    :target: https://travis-ci.org/quipucords/quipucords
.. image:: https://coveralls.io/repos/github/quipucords/quipucords/badge.svg?branch=master
    :target: https://coveralls.io/github/quipucords/quipucords?branch=master


quipucords - Tool for discovery, inspection, collection/deduplication, and reporting on an IT environment
==========================================================================================================

quipucords is a tool for discovery, inspection, collection/deduplication, and
reporting on an IT environment.


This *README* contains information about running and development of quipucords,
basic usage, known issues, and best practices.

- `Intro to quipucords`_
- `Requirements & Assumptions`_
- `Installation`_
- `Command Syntax & Usage`_
- `Development`_
- `Issues`_
- `Changes`_
- `Authors`_
- `Contributing`_
- `Copyright & License`_


Intro to quipucords
-------------------
quipucords is a *Python* based information gathering tool. quipucords provides a
server base infrastructure for process tasks that discover and inspect remote
systems utilizing *Ansible* while additionally looking to integrate and extract
data from management engines. quipucords collects basic information about the
operating system, hardware, and application data for each system. quipucords is
intended to help simplify some basic sysadmin tasks, like
managing licensing renewals and new deployments.


Requirements & Assumptions
--------------------------
Before installing quipucords, there are some guidelines about which system it should be installed on:
 * quipucords is written to run on RHEL or Fedora servers.
 * The system that quipucords is installed on must have access to the source systems to be discovered and inspected.
 * The target systems must be running SSH.
 * The user account that quipucords uses to SSH into the systems must have adequate permissions to run commands and read certain files.
 * The user account quipucords uses for a machine should have a sh like shell. For example, it *cannot* be a /sbin/nologin or /bin/false shell.

The python packages required for running quipucords on a system can be found in
 the ``requirements.txt`` file. The python packages required to build & test
 quipucords from source can be found in the ``requirements.txt`` and
 ``dev-requirements.txt`` files.

Installation
------------
quipucords is delivered via a RPM command line tool and a server container image. Below you will find instructions for installing each of these items.

Command Line
^^^^^^^^^^^^
qpc is available for `download <https://copr.fedorainfracloud.org/coprs/chambridge/qpc/>`_ from fedora COPR.

1. First, make sure that the EPEL repo is enabled for the server.
You can find the appropriate architecture and version on the `EPEL wiki <https://fedoraproject.org/wiki/EPEL>`_::

 rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

2. Next, add the COPR repo to your server.
You can find the appropriate architecture and version on the `COPR qpc page <https://copr.fedorainfracloud.org/coprs/chambridge/qpc/>`_::

 wget -O /etc/yum.repos.d/chambridge-qpc-epel-7.repo https://copr.fedorainfracloud.org/coprs/chambridge/qpc/repo/epel-7/chambridge-qpc-epel-7.repo

3. Then, install the qpc package:

``yum -y install qpc``

Container Image
^^^^^^^^^^^^^^^
The quipucords container image can be created from source. This repository contains a Dockerfile detailing the image creation of the server.
You must have `Docker installed <https://docs.docker.com/engine/installation/>`_ in order to create the image and run the container.

1. Begin by cloning the repository::

    git clone git@github.com:quipucords/quipucords.git

2. Build the docker image::

    docker -D build . -t quipucords:latest

*Note: You may or may not need to use ``sudo`` depending on your install setup.*

3. Run the docker image::

    docker run -d -p443:443 -i quipucords:latest

Now the server should be running and you can launch the `login <https://127.0.0.1/>`_.
You can work with the APIs directly or you can use the CLI. You can configure the CLI with the following command::

    qpc server config --host 127.0.0.1


Command Syntax & Usage
----------------------
The complete list of options for each command and subcommand are listed in the
qpc manpage with other usage examples.

For expanded information on credential entries, sources, scanning, and output read
the `syntax and usage document <docs/source/man.rst>`_.

Development
-----------
Begin by cloning the repository::

    git clone git@github.com:quipucords/quipucords.git

quipucords currently supports Python 3.5, 3.6. If you don't have Python on your
system follow these `instructions <https://www.python.org/downloads/>`_. Based
on your system you may be using either `pip` or `pip3` to install modules, for
simplicity the instructions below will specify `pip`.


Virtual Environment
^^^^^^^^^^^^^^^^^^^
You may wish to isolate your development using a virtual environment. Run the
following command to setup an virtual environment::

    virtualenv -p python3 venv
    source venv/bin/activate


Installing Dependencies
^^^^^^^^^^^^^^^^^^^^^^^
From within the local clone root directory run the following command to install
dependencies needed for development and testing purposes:

First, you need to collect some packages available through either `yum` (RHEL)
or `dnf` (fedora)::

    sudo yum install python-tools

The rest of the packages can be installed locally in your virtual environment::

    pip install -r requirements.txt


Linting
^^^^^^^
In order to lint changes made to the source code execute the following command::

    make lint


Initialize Server
^^^^^^^^^^^^^^^^^
In order to setup the server execute the following command::

    make server-init

This command will create a super user with name *admin* and password of *pass*.

Running Server
^^^^^^^^^^^^^^
In order to run the server execute the following command::

    make serve

In order to login to the server you must launch to http://127.0.0.1:8000/admin/ and provide the super user credentials.
From here you can change the password and also go to some fo the browsable APIs like http://127.0.0.1:8000/api/v1/credentials/.
Using the CLI you can configure access to the server using `qpc server config` and login using `qpc server login`.

If you intend to run on Mac OS there are several more steps required.

- You need to increase the maxfile limit as described `here <https://github.com/ansible/ansible/issues/12259#issuecomment-173371493>`_.
- Install sshpass as described `here <https://github.com/ansible-tw/AMA/issues/21>`_.
- Install coreutils to obtains the gtimeout command.  Run: `brew install coreutils`
- If you are running macOS 10.13 or greater and you encounter unexpected crashes when running scans,
  set the environment variable ``OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`` before starting the server.
  See explanation `here <https://github.com/ansible/ansible/issues/31869#issuecomment-337769174>`_.


Testing
^^^^^^^

Unit Testing
""""""""""""

To run the unit tests with the interpreter available as ``python``, use::

    make test


Issues
------
To report bugs for quipucords `open issues <https://github.com/quipucords/quipucords/issues>`_
against this repository in Github. Please complete the issue template when
opening a new bug to improve investigation and resolution time.


Changes
-------
Track & find changes to the tool in `CHANGES <CHANGES.rst>`_.


Authors
-------
Authorship and current maintainer information can be found in `AUTHORS <AUTHORS.rst>`_.


Contributing
------------
Reference the `CONTRIBUTING <CONTRIBUTING.rst>`_ guide for information to the project.


Copyright & License
-------------------
Copyright 2017-2018, Red Hat, Inc.

quipucords is released under the `GNU Public License version 3 <LICENSE>`_.
