.. image:: https://travis-ci.org/quipucords/quipucords.svg?branch=master
    :target: https://travis-ci.org/quipucords/quipucords
.. image:: https://codecov.io/gh/quipucords/quipucords/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/quipucords/quipucords
.. image:: https://landscape.io/github/quipucords/quipucords/master/landscape.svg?style=flat
   :target: https://landscape.io/github/quipucords/quipucords/master
   :alt: Code Health
.. image:: https://requires.io/github/quipucords/quipucords/requirements.svg?branch=master
    :target: https://requires.io/github/quipucords/quipucords/requirements/?branch=master
    :alt: Requirements Status
.. image:: https://readthedocs.org/projects/quipucords/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://quipucords.readthedocs.io/en/latest/?badge=latest
.. image:: https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/package/qpc/status_image/last_build.png
    :alt: CLI RPM Build Status
    :scale: 100%
    :target: https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/

quipucords - Tool for discovery, inspection, collection, deduplication, and reporting on an IT environment
===================================================================================================================

quipucords is a tool for discovery, inspection, collection, deduplication, and reporting on an IT environment.


This *README* file contains information about the installation and development of quipucords, as well as instructions about where to find basic usage, known issue, and best practices information.

- `Introduction to quipucords`_
- `Requirements and Assumptions`_
- `Installation`_
- `Command Syntax and Usage`_
- `Development`_
- `Issues`_
- `Changes`_
- `Authors`_
- `Contributing`_
- `Copyright and License`_


Introduction to quipucords
--------------------------
quipucords is a *Python* based information gathering tool. quipucords provides a server base infrastructure for process tasks that discover and inspect remote systems by utilizing *Ansible* while additionally looking to integrate and extract data from systems management solutions. quipucords collects basic information about the operating system, hardware, and application data for each system. quipucords is intended to help simplify some of the basic system administrator tasks that are a part of the larger goal of managing licensing renewals and new deployments.


Requirements and Assumptions
----------------------------
Before installing quipucords on a system, review the following guidelines about installing and running quipucords:

 * quipucords is written to run on RHEL or Fedora servers.
 * The system that quipucords is installed on must have access to the systems to be discovered and inspected.
 * The target systems must be running SSH.
 * The user account that quipucords uses for the SSH connection into the target systems must have adequate permissions to run commands and read certain files, such as privilege escalation required for the ``systemctl`` command.
 * The user account that quipucords uses for a machine requires an sh shell or a similar shell. For example, the shell *cannot* be a /sbin/nologin or /bin/false shell.

The Python packages that are required for running quipucords on a system can be found in the ``requirements.txt`` file. The Python packages that are required to build and test quipucords from source can be found in the ``requirements.txt`` and ``dev-requirements.txt`` files.

Installation
------------
quipucords is delivered with an RPM command line tool and a server container image. The following information contains instructions for installing each of these items.

Command Line
^^^^^^^^^^^^
qpc is available for `download <https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/>`_ from the Fedora COPR.

1. Enable the EPEL repo for the server. You can find the appropriate architecture and version on the `EPEL wiki <https://fedoraproject.org/wiki/EPEL>`_::

    rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

2. Add the COPR repo to your server. You can find the appropriate architecture and version on the `COPR qpc page <https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/>`_::

    wget -O /etc/yum.repos.d/group_quipucords-qpc-epel-7.repo \
    https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/repo/epel-7/group_quipucords-qpc-epel-7.repo

3. Install the qpc package::

    yum -y install qpc

Container Image
^^^^^^^^^^^^^^^
The quipucords container image can be created from source. This quipucords repository includes a Dockerfile that contains instructions for the image creation of the server.
You must have `Docker installed <https://docs.docker.com/engine/installation/>`_ to create the image and run the container.

1. Clone the repository::

    git clone git@github.com:quipucords/quipucords.git

2. *Optional* - Build UI.::

    make build-ui

  **NOTE:** You will need to install NodeJS.  See `<https://nodejs.org/>`_.

3. Build the Docker image::

    docker -D build . -t quipucords:latest

  **NOTE:** The need to use ``sudo`` for this step is dependent upon on your system configuration.

4. Run the Docker image::

    docker run -d -p443:443 -i quipucords:latest

5. Configure the CLI by using the following commands::

    qpc server config --host 127.0.0.1
    qpc server login

6.  You can work with the APIs, the CLI, and UI (visit `<https://127.0.0.1/>`_ if you installed the UI in step 2 above).

Running quipucords server in gunicorn
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can run the server locally inside of gunicorn.  This can be a useful way to debug.

1. Clone the repository::

    git clone git@github.com:quipucords/quipucords.git

2. Switch to quipucords directory::

    cd quipucords

3. Make symbolic link to ansible roles::
    ln -s ../roles/ roles

4. Install gunicorn::
    pip install gunicorn==19.7.1

5. Start gunicorn::
    gunicorn quipucords.wsgi -c ./local_gunicorn.conf.py

6. Configure the CLI by using the following commands::
    qpc server config --host 127.0.0.1 --port 8000
    qpc server login

Command Syntax and Usage
------------------------
The complete list of options for each qpc command and subcommand are listed in the qpc man page. The man page information also contains usage examples and some best practice recommendations.

For expanded information on credential entries, sources, scanning, and output, see the `syntax and usage document <docs/source/man.rst>`_.

Development
-----------
To work with the quipucords code, begin by cloning the repository::

    git clone git@github.com:quipucords/quipucords.git

quipucords currently supports Python 3.5 and 3.6. If you do not have Python on your system, follow these `instructions <https://www.python.org/downloads/>`_. Based on the configuration of your system, you might be using either `pip` or `pip3` to install modules. The following instructions show the steps for a system with `pip`.


Setting Up a Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You might want to isolate your development work by using a virtual environment. Run the following command to set up a virtual environment::

    virtualenv -p python3 venv
    source venv/bin/activate


Installing Dependencies
^^^^^^^^^^^^^^^^^^^^^^^
Run the following commands from within the local clone root directory to install dependencies that are needed for development and testing purposes:

1. Collect some packages available through either `yum` (for RHEL) or `dnf` (for Fedora)::

    sudo yum install python-tools

2. Install the rest of the packages locally in your virtual environment::

    pip install -r requirements.txt


Linting
^^^^^^^
To lint changes that are made to the source code, run the following command::

    make lint


Initializing the Server
^^^^^^^^^^^^^^^^^^^^^^^
To set up the server, run the following command::

    make server-init

This command creates a superuser with name *admin* and password of *pass*.

Running the Server
^^^^^^^^^^^^^^^^^^
To run the development server, run the following command::

    make serve

To log in to the server, you must connect to http://127.0.0.1:8000/admin/ and provide the superuser credentials.

After logging in, you can change the password and also go to some of the browsable APIs such as http://127.0.0.1:8000/api/v1/credentials/.
To use the command line interface, you can configure access to the server by entering `qpc server config`. You can then log in by using `qpc server login`.

If you intend to run on Mac OS, there are several more steps that are required.

- Increase the maxfile limit as described `here <https://github.com/ansible/ansible/issues/12259#issuecomment-173371493>`_.
- Install sshpass as described `here <https://github.com/ansible-tw/AMA/issues/21>`_.
- Install coreutils to obtain the gtimeout command. To do this step, run the `brew install coreutils` command.
- If you are running macOS 10.13 or later and you encounter unexpected crashes when running scans,
  set the environment variable ``OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`` before starting the server.
  See the explanation for this step `here <https://github.com/ansible/ansible/issues/31869#issuecomment-337769174>`_.


Testing
^^^^^^^

Unit Testing
""""""""""""

To run the unit tests with the interpreter available as ``python``, use the following command::

    make test


Issues
------
To report bugs for quipucords `open issues <https://github.com/quipucords/quipucords/issues>`_ against this repository in Github. Complete the issue template when opening a new bug to improve investigation and resolution time.


Changes
-------
Track and find changes to the tool in `CHANGES <CHANGES.rst>`_.


Authors
-------
Authorship and current maintainer information can be found in `AUTHORS <AUTHORS.rst>`_.


Contributing
------------
See the `CONTRIBUTING <CONTRIBUTING.rst>`_ guide for information about contributing to the project.


Copyright and License
---------------------
Copyright 2017-2018, Red Hat, Inc.

quipucords is released under the `GNU Public License version 3 <LICENSE>`_.
