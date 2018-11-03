Scripted Installation
----------------------
The scripted installation runs an installer that uses Ansible to install the command line tool and container image and any associated dependencies.

**IMPORTANT:** Red Hat Enterprise Linux 7 users must enable the `Extras <https://access.redhat.com/solutions/912213>`_ (``rhel-7-server-extras-rpms``) and `Optional <https://access.redhat.com/solutions/265523>`_ (``rhel-7-server-optional-rpms``) repositories to use the scripted installation.

When you run the scripted installation, the server is installed and started as described in `Configuring and Starting Quipucords <install.html#config-and-start>`_. However, you can also run the scripted installation with options if you want to change some of the defaults.

Installing the Ansible Prerequisite
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Prepare the system to install the software by installing Ansible. For more information, see the `Ansible installation documentation <http://docs.ansible.com/ansible/latest/intro_installation.html#installing-the-control-machine>`_.

Obtaining the Installer
^^^^^^^^^^^^^^^^^^^^^^^
After Ansible is installed, use the following steps to obtain the installer for the Quipucords command line tool and server.

1. Download the installer by entering the following command::

    # curl -k -O -sSL https://github.com/quipucords/quipucords/releases/download/0.0.45/quipucords.install.tar.gz

2. Extract the installer by entering the following command::

    # tar -xvzf quipucords.install.tar.gz

Running the Installer
^^^^^^^^^^^^^^^^^^^^^
You can run the installer in different ways, depending on your needs:

- You can run with internet connectivity to download necessary packages or set up and pull for needed repositories. This choice is the recommended approach because it simplifies the installation.

- You can download the RPM packages and container image and place them in a specified directory. This choice is useful when you are installing on systems with limited or no access to the internet.

Installing with Internet Connectivity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you choose the internet connectivity option, use the following steps to run the installer.

1. Change to the installer directory by entering the following command::

    # cd install/

2. Start the installation by entering the following command. Alternatively, enter the following command with options as described in `Installation Options`_::

    # ./install.sh

The output appears similar to the following example::

    Installation complete.

Next Steps
++++++++++
When the installation completes, the Quipucords server is installed and started. In addition, a connection to the command line tool is configured on the same system on which the server is installed. However, you must still complete the following steps before you can begin using Quipucords:

- `Changing the Default Password for the Quipucords Server <install.html#change-default-pw>`_
- `Logging in to the Quipucords Server <cli_server_interaction.html#login>`_

Installing with Downloaded Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you choose the downloaded packages option to run the installer, you must first gather the necessary packages. Then use the following steps to run the installer.

To install the server, you must have the following items. For more information about download locations for specific operating systems, see `Installing the Quipucords Server Container Image <install.html#container>`_.

- Docker package
- Server container image

To install the command line tool, you must have the following items. For more information about download locations for specific operating systems, see `Installing the Quipucords Command Line Tool <install.html#commandline>`_.

- EPEL package
- QPC package

1. Change to the installer directory by entering following command::

    # cd install/

2. Create a ``packages`` directory to use to install the downloaded packages by entering the following command::

    # mkdir packages

3. Copy the downloaded packages into the ``packages`` directory by entering the following command::

    # cp /path/to/package ./packages/

4. Start the installation by entering the following command. Alternatively, enter the following command with options as described in `Installation Options`_::

    # ./install.sh

The output appears similar to the following example::

    Installation complete.

Next Steps
++++++++++
When the installation completes, the Quipucords server is installed and started. In addition, a connection to the command line tool is configured on the same system on which the server is installed. However, you must still complete the following steps before you can begin using Quipucords:

- `Changing the Default Password for the Quipucords Server <install.html#change-default-pw>`_
- `Logging in to the Quipucords Server <cli_server_interaction.html#login>`_

Installation Options
~~~~~~~~~~~~~~~~~~~~
The installer has various options, each of which has a default value. You can either run the installer with no options to use all the default values, or provide values for one or more of these options. You can pass values for these options by using the ``-e`` flag when you run the command to start the installer, as shown in the following example::

    # ./install.sh -e option1=value1 -e option2=value2 ...

Options:
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
