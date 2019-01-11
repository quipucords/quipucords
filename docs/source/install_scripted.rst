Scripted Installation
----------------------
The scripted installation runs an installer that uses Ansible to install the command line tool, quipucords server image, and the database image. When you run the scripted installation, the server is installed and started as described in `Configuring and Starting Quipucords <install.html#config-and-start>`_. However, you can change some of the defaults used by the scripted installation with the `Installation Options <install.html#installation-options>`_ .

Obtaining the Installer
^^^^^^^^^^^^^^^^^^^^^^^
1. Download the installer by entering the following command::

    # curl -k -O -sSL https://github.com/quipucords/quipucords/releases/download/0.0.46/quipucords.install.0.0.46.tar.gz

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

2. Start the installation by entering the following command. Alternatively, enter the following command with options as described in `Installation Options`_::

    # ./install.sh

The output appears similar to the following example::

    Installation complete.

Installing without Internet Connectivity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you choose the offline option to run the installer, these associated dependencies must be installed.

**Server Dependencies:**

- `Ansible <install.html#installing-the-ansible-prerequisite>`_
- `Docker <install.html#installing-docker-and-the-quipucords-server-container-image>`_

**Command Line Tool Dependencies:**

- `Download & Configure EPEL <install.html#commandline>`_
- Python 3.4
- Python 3.4-requests

Packages
++++++++
After the dependencies are installed, you must gather packages through the `Github Release Page <https://github.com/quipucords/quipucords/releases/tag/0.0.46>`_.

**Server Packages:**

- Server Container Image (quipucords.version.tar.gz)
- Postgres Container Image (postgres.version.tar.gz)
- **Note:** You must extract the tarball to access the postgres image with the command::

  # tar -xzvf postgres.version.tar.gz

**Command Line Tool RPM Package:**

- QPC Package (all of the qpc-version.rpm)


1. Change to the installer directory by entering following command::

    # cd install/

2. Create a ``packages`` directory to use to install the downloaded packages by entering the following command::

    # mkdir packages

3. Move the downloaded packages into the ``packages`` directory by entering the following command::

    # mv /path/to/package ./packages/

4. Start the installation by entering the following command. Alternatively, enter the following command with options as described in `Installation Options`_::

    # ./install.sh -e install_offline=true

The output appears similar to the following example::

    Installation complete.

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
    - Contains the port number for the Quipucords server. Defaults to ``443``.
 - **server_name**
    - Contains the name for the Quipucords server. Defaults to ``quipucords``.
 - **QPC_SERVER_TIMEOUT**
    - Contains the HTTP timeout length for the Quipucords server. Defaults to ``120``.
 - **QPC_DBMS_USER**
    - (Optional) Specifies the database user for postgres. Defaults to ``postgres``.
 - **QPC_DBMS_PASSWORD**
    - (Optional) Specifies the database password for postgres. Defaults to ``password``.