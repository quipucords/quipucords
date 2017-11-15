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
 * The system that quipucords is installed on must have network access the systems to be discovered and inspected.
 * The target systems must be running SSH.
 * The user account that quipucords uses to SSH into the systems must have adequate permissions to run commands and read certain files.
 * The user account quipucords uses for a machine should have a sh like shell. For example, it *cannot* be a /sbin/nologin or /bin/false shell.

The python packages required for running quipucords on a system can be found in
 the ``requirements.txt`` file. The python packages required to build & test
 quipucords from source can be found in the ``requirements.txt`` and
 ``dev-requirements.txt`` files.

Command Syntax & Usage
----------------------
The complete list of options for each command and subcommand are listed in the
qpc manpage with other usage examples.

For expanded information on auth entries, profiles, scanning, and output read
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


Running Server
^^^^^^^^^^^^^^
In order to run the server execute the following command::

    make serve

If you intend to run on Mac OS there are several more steps required.
- You need to increase the maxfile limit as described `here <https://github.com/ansible/ansible/issues/12259#issuecomment-173371493>`_.
- Install sshpass as described `here <https://github.com/ansible-tw/AMA/issues/21>`_.


Piping data to Elasticsearch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Before starting the server, set the following environment variables::

    USE_ELASTICSEARCH=True
    ES_HOSTS=http://ES_HOST1,http://ES_HOST2

Additionally, there is a `docker-compose.yml` file located in the `elasticsearch` directory. To start a local docker image do the following:
 * Ensure you have docker and docker-compose installed
 * Open a terminal window and switch to the `elasticsearch` folder
 * Run `docker-compose up` to start Elasticsearch and Kibana
 * Run `docker-compose down` to stop Elasticsearch and Kibana


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
Copyright 2017, Red Hat, Inc.

quipucords is released under the `GNU Public License version 3 <LICENSE>`_.
