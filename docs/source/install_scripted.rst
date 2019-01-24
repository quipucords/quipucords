Scripted Installation
----------------------
The scripted installation runs an installer that uses Ansible to install the command line tool, quipucords server image, and the database image. When you run the scripted installation, the server is installed and started as described in `Configuring and Starting Quipucords <install.html#config-and-start>`_. However, you can change some of the defaults used by the scripted installation with the `Installation Options <install.html#install-opts>`_.

Obtaining the Installer
^^^^^^^^^^^^^^^^^^^^^^^
1. Download the installer by entering the following command::

    # curl -k -O -sSL https://github.com/quipucords/quipucords/releases/download/0.0.47/quipucords.install.0.0.47.tar.gz

2. Extract the installer by entering the following command::

    # tar -xvzf quipucords.install.tar.gz

Running the Installer
^^^^^^^^^^^^^^^^^^^^^
You can run the installer in different ways, depending on your needs:

- **Online:** You can run with internet connectivity to install any associated dependencies, download required packages, and pull for needed repositories. This choice is the recommended approach because it simplifies the installation.

- **Offline:** You can run the installer offline by manually installing dependencies, downloading RPM packages and container images and placing them into a specified directory. This choice is useful when you are installing on systems with limited or no access to the internet.

Installing with Internet Connectivity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you choose the internet connectivity option, use the following steps to run the installer.

1. Change to the installer directory by entering the following command::

    # cd install/

2. Start the installation by entering the following command. Alternatively, enter the following command with options as described in `Installation Options <install.html#install-opts>`_::

    # ./install.sh

The output appears similar to the following example::

    Installation complete.

Installing without Internet Connectivity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you choose the offline option to run the installer, you will need to obtain the following packages on a machine with internet connectivity.

**Quipucords Server Package:**

- Server Container Image (`Download <https://github.com/quipucords/quipucords/releases/download/0.0.47/quipucords.0.0.47.tar.gz>`_)

**Build the Postgres Docker Image:**

The Quipucords server requires a Postgres Docker image.  You must build the Docker image on a machine with internet connectivity.  Follow the steps documented below to create a Postgres Docker image.

- Install Docker (`Documentation <https://docs.docker.com/install/>`_)
- Create the postgres image tar with the following commands::

      # docker pull postgres:9.6.10
      # docker save -o postgres.9.6.10.tar postgres:9.6.10

**Note:** The offline installation script requires the postgres tar to be named ``postgres.9.6.10.tar``.

**Command Line Tool RPM Package:**

- RHEL & Centos 6 (`Download <https://github.com/quipucords/qpc/releases/download/0.0.47/qpc-0.0.47-ACTUAL_COPR_GIT_COMMIT.el6.noarch.rpm>`_)
- RHEL & Centos 7 (`Download <https://github.com/quipucords/qpc/releases/download/0.0.47/qpc-0.0.47-ACTUAL_COPR_GIT_COMMIT.el7.noarch.rpm>`_)
- Fedora 27 (`Download <https://github.com/quipucords/qpc/releases/download/0.0.47/qpc-0.0.47-ACTUAL_COPR_GIT_COMMIT.fc27.noarch.rpm>`_)
- Fedora 28 (`Download <https://github.com/quipucords/qpc/releases/download/0.0.47/qpc-0.0.47-ACTUAL_COPR_GIT_COMMIT.fc28.noarch.rpm>`_)

**Transfer Packages**

After the required packages have been collected, they will need to be transferred to the machine where the Quipucords server will be installed.

1. Change to the installer directory by entering following command::

    # cd install/

2. Create a ``packages`` directory to use to install the downloaded packages by entering the following command::

    # mkdir packages

3. Move the downloaded packages into the ``packages`` directory by entering the following command::

    # mv /path/to/package ./packages/

Offline Dependencies:
+++++++++++++++++++++

The following associated dependencies must be installed onto the offline machine before the installation script can be executed.

**Server Dependencies:**

- `Ansible <install.html#installing-the-ansible-prerequisite>`_
- `Docker <install.html#installing-docker-and-the-quipucords-server-container-image>`_

**Command Line Tool Dependencies:**

- `Download & Configure EPEL <install.html#commandline>`_
- Python 3.4
- Python 3.4-requests

**Start Offline Install**

Start the offline installation by entering the following command. Alternatively, enter the following command with options as described in `Installation Options`_::

    # ./install.sh -e install_offline=true

The output appears similar to the following example::

    Installation complete.


.. _install-opts:

Installation Options
~~~~~~~~~~~~~~~~~~~~
The installer has various options, each of which has a default value. You can either run the installer with no options to use all the default values, or provide values for one or more of these options. You can pass values for these options by using the ``-e`` flag when you run the command to start the installer, as shown in the following example::

    # ./install.sh -e option1=value1 -e option2=value2 ...

Options:
 - **install_offline**
    - Contains a ``true`` or ``false`` value. Defaults to ``false``. Supply ``true`` to start an offline installation.
 - **use_supervisord**
    - Contains a ``true`` or ``false`` value. Defaults to ``true``. Supply ``false`` to start server without supervisord.
 - **install_server**
    - Contains a ``true`` or ``false`` value. Defaults to ``true``. Supply ``false`` to skip the installation of the server.
 - **install_cli**
    - Contains a ``true`` or ``false`` value. Defaults to ``true``. Supply ``false`` to skip the installation of the command line tool.
 - **pkg_install_dir**
    - Contains the fully qualified path to the downloaded packages for the installer. Defaults to ``<installer>/packages/``.
 - **server_install_dir**
    - Contains the fully qualified path to the installation directory for the Quipucords server. Defaults to ``~/quipucords/``.
 - **server_port**
    - Contains the port number for the Quipucords server. Defaults to ``9443``.
 - **server_name**
    - Contains the name for the Quipucords server. Defaults to ``quipucords``.
 - **QPC_SERVER_TIMEOUT**
    - Contains the HTTP timeout length for the Quipucords server. Defaults to ``120``.
 - **QPC_DBMS_USER**
    - (Optional) Specifies the database user for postgres. Defaults to ``postgres``.
 - **QPC_DBMS_PASSWORD**
    - (Optional) Specifies the database password for postgres. Defaults to ``password``.
