Scripted Installation
----------------------
The scripted installation utilizes Ansible to install the command line and container image and any associated dependencies.


**TIP:** *Red Hat Enterprise Linux 7* users will need to enable the `Extras <https://access.redhat.com/solutions/912213>`_ ( ``rhel-7-server-extras-rpms`` ) and `Optional <https://access.redhat.com/solutions/265523>`_ ( ``rhel-7-server-optional-rpms`` ) repositories.

Installing the Ansible Prerequisite
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Follow the `Ansible installation documentation <http://docs.ansible.com/ansible/latest/intro_installation.html#installing-the-control-machine>`_ to prepare the system to install the software.

Obtaining the Installer
^^^^^^^^^^^^^^^^^^^^^^^
After Ansible is installed, you can obtain the installer that enables the use of the Quipucords command line and server.

1. Download the installer by entering the following command::

    # curl -k -O -sSL https://github.com/quipucords/quipucords/releases/download/1.0.0/quipucords.install.tar.gz

2. Unzip the installer with the following command::

    # tar -xvzf quipucords.install.tar.gz

Executing the Installer
^^^^^^^^^^^^^^^^^^^^^^^
You can install in different ways, depending on your needs:

- You can run with internet connectivity which will download necessary packages or setup and pull for needed repositories. This choice is the recommended approach because it simplifies the installation.

- You can download the RPM packages and container image and place them in a specified directory. This choice is useful when installing on systems with limited or no access to the internet.

Installing with Internet Connectivity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You are now prepared to run the installer.

1. Change into the installer directory with the following command::

    # cd install/

2. To start the installation you can run the following command::

    # ./install.sh

The output appears similar to the following example::

    Installation complete.

When the installation is complete the server will be installed and started as described in the `Configuring and Starting Quipucords <install.html#config-and-start>`_ section.

Installing with Downloaded Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You must first gather the necessary packages.

In order to install the server you will need the following items, see `Installing the Quipucords Server Container Image <install.html#container>`_ for download locations for specific operating systems:

- Docker package
- Server container image

In order to install the command line you will need the following items, see `Installing the Quipucords Command Line Tool <install.html#commandline>`_ for download locations for specific operating systems:

- EPEL package
- QPC package

1. Change into the installer directory with the following command::

    # cd install/

2. Create a directory ``packages`` to install downloaded packages from with the following command::

    # mkdir packages

3. Copy the downloaded packages into the ``packages`` directory by running the following commands::

    # cp /path/to/package ./packages/

4. To start the installation you can run the following command::

    # ./install.sh

The output appears similar to the following example::

    Installation complete.

When the installation is complete the server will be installed and started as described in the `Configuring and Starting Quipucords <install.html#config-and-start>`_ section.

Install Options
~~~~~~~~~~~~~~~
The installer allows for various options. Each of the options can be passed with a ``-e`` flag when executing the installer as follows::

    # ./install.sh -e option1=value1 -e option2=value2 ...

Options:
 - **install_server**
    - ``true | false`` - Defaults to true, supply ``false`` to skip installing the server
 - **install_cli**
    - ``true | false`` - Defaults to true, supply ``false`` to skip installing the command line
 - **pkg_install_dir**
    - ``fully-quailified path`` - Defaults to ``<installer>/packages/``
 - **server_install_dir**
    - ``fully-quailified path`` - Defaults to ``~/quipucords/``
 - **server_port**
    - ``port number`` - Defaults to 443
 - **server_name**
    - ``name`` - Defaults to ``quipucords``
