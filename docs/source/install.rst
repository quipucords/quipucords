Installing Quipucords
=====================
Quipucords is delivered in two parts, a command line tool as an RPM package and a server as a container image. The following instructions describe how to install the parts of Quipucords using a scripted installation or step by step commands.

Scripted Installation
----------------------
The scripted installation utilizes Ansible to install the command line and container image and any associated dependencies.

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

.. _commandline:

Installing the Quipucords Command Line Tool
-------------------------------------------
qpc, the command line tool that is installed by RPM, is available for `download <https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/>`_ from the Fedora COPR build and repository system.

1. Enable the EPEL repo for the server. You can find the appropriate architecture and version on the `EPEL wiki <https://fedoraproject.org/wiki/EPEL>`_.

  - For Red Hat Enterprise Linux 7 or CentOS 7, enter the following command::

      # rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

  - For Red Hat Enterprise Linux 6 or CentOS 6, enter the following command::

      # rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm

2. Add the COPR repo to your server. You can find the appropriate architecture and version on the `COPR qpc page <https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/>`_.


  - For Red Hat Enterprise Linux 7 or CentOS 7, enter the following command::

      # wget -O group_quipucords-qpc-epel-7.repo https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/repo/epel-7/group_quipucords-qpc-epel-7.repo

  - For Red Hat Enterprise Linux 6 or CentOS 6, enter the following command::

      # wget -O /etc/yum.repos.d/group_quipucords-qpc-epel-6.repo https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/repo/epel-6/group_quipucords-qpc-epel-6.repo

  - For Fedora 27, enter the following command::

      # wget -O /etc/yum.repos.d/group_quipucords-qpc-fedora-27.repo https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/repo/fedora-27/group_quipucords-qpc-fedora-27.repo

  - For Fedora 26, enter the following command::

      # wget -O /etc/yum.repos.d/group_quipucords-qpc-fedora-26.repo https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/repo/fedora-26/group_quipucords-qpc-fedora-26.repo

3. Install the qpc package:

  - Enter the following command::

      # yum -y install qpc


Installing the Quipucords Server Requirement and Container Image
----------------------------------------------------------------
The Quipucords server is delivered as a container image that runs on your server. First you must install and start the necessary prerequisite, Docker, to run the container. Then you can obtain and install the Quipucords server container image.

Installing the Docker Prerequisite
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The instructions for installing Docker vary according to your system configuration.

Installing Docker on Red Hat Enterprise Linux 7 or CentOS 7
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
You can install Docker in different ways, depending on your needs:

- You can set up the Docker repositories and then install from them. This choice is the recommended approach because it simplifies the installation and upgrade tasks.

- You can download the RPM package, install it manually, and manage upgrades manually. This choice is useful when Docker is installed on systems with limited or no access to the internet.

Installing from the repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

2. Install the required packages::

    # sudo yum install -y yum-utils device-mapper-persistent-data lvm2

3. Add the repository::

    # sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

4. Install Docker from the repository::

    # sudo yum install docker-ce

Installing from a package
~~~~~~~~~~~~~~~~~~~~~~~~~
1. Go to https://download.docker.com/linux/centos/7/x86_64/stable/Packages/. For the Docker version that you want to install, download the RPM package to the intended installation system.

2. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

3. Install Docker, changing the path in the following example to the path where you downloaded the Docker package::

    # sudo yum install /path/to/package.rpm

Starting Docker on Red Hat Enterprise Linux 7 or CentOS 7
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After you install Docker, you must start it and verify that it is running.

1. Start Docker::

    # sudo systemctl start docker

2. Verify that Docker is installed correctly. To do this step, run the hello-world image::

    # sudo docker run hello-world

After you complete the steps to install Docker for Red Hat Enterprise Linux 7 or CentOS 7, continue with the Quipucords server installation steps in `Installing the Quipucords Server Container Image <install.html#container>`_.

Installing Docker on Red Hat Enterprise Linux 6.6+ or CentOS 6.6+
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
To install Docker on Red Hat Enterprise Linux 6.6+ or CentOS 6.6+, you must have kernel 2.6.32-431 or later installed.

To check the current kernel release, open a terminal session and use the ``uname`` command to display the kernel release information, as shown in the following example::

    # uname -r

The output of this command is similar to the following example::

  2.6.32-573.el6.x86_64

**TIP:** After you confirm that you have at least the minimum required kernel release, it is recommended that you fully update your system. Having a fully patched system can help you avoid kernel bugs that have already been fixed on the latest kernel packages.

When your system meets the minimum required kernel release, you can use the following steps to install Docker:

1. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

2. Download the Docker RPM package to the current directory::

    # curl -k -O -sSL https://yum.dockerproject.org/repo/main/centos/6/Packages/docker-engine-1.7.1-1.el6.x86_64.rpm

3. Install the required packages::

    # sudo yum install -y yum-utils device-mapper-persistent-data lvm2 libcgroup xz

4. Install the Docker package with yum::

    # sudo yum localinstall --nogpgcheck docker-engine-1.7.1-1.el6.x86_64.rpm

Starting Docker on Red Hat Enterprise Linux 6.6+ or CentOS 6.6+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After you install Docker, you must start it and verify that it is running.

1. Start the Docker daemon::

    # sudo service docker start

2. Verify that Docker is installed correctly. To do this step, run the hello-world image::

    # sudo docker run hello-world

This command displays output similar to the following truncated example. The first section of the output contains a message about the installation status::

    Unable to find image 'hello-world:latest' locally
    latest: Pulling from hello-world
    a8219747be10: Pull complete
    91c95931e552: Already exists
    hello-world:latest: The image you are pulling has been verified. Important: image verification is a tech preview feature and should not be relied on to provide security.
    Digest: sha256:aa03e5d0d5553b4c3473e89c8619cf79df368babd18681cf5daeb82aab55838d
    Status: Downloaded newer image for hello-world:latest
    Hello from Docker.
    This message shows that your installation appears to be working correctly.

    ...


3. To ensure that Docker starts when you start your system, enter the following command::

    # sudo chkconfig docker on

After you complete the steps to install Docker for Red Hat Enterprise Linux 6.6+ or CentOS 6.6+, you can continue with the Quipucords server installation steps in `Installing the Quipucords Server Container Image <install.html#container>`_.


Installing Docker on Fedora 26 or Fedora 27
"""""""""""""""""""""""""""""""""""""""""""
You can install Docker in different ways, depending on your needs:

- You can set up the Docker repositories and then install from them. This choice is the recommended approach because it simplifies the installation and upgrade tasks.

- You can download the RPM package, install it manually, and manage upgrades manually. This choice is useful when Docker is installed on systems with limited or no access to the internet.

Installing from the repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

2. Install the required packages::

    # sudo dnf -y install dnf-plugins-core

3. Add the repository::

    # sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo

4. Install Docker from the repository::

    # sudo dnf install docker-ce

Installing from a package
~~~~~~~~~~~~~~~~~~~~~~~~~
1. Go to https://download.docker.com/linux/fedora/. For the Docker version that you want to install, download the RPM package to the intended installation system.

2. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

3. Install Docker, changing the path in the following example to the path where you downloaded the Docker package::

    # sudo yum install /path/to/package.rpm

Starting Docker on Fedora 26 or Fedora 27
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After you install Docker, you must start it and verify that it is running.

1. Start Docker::

    # sudo systemctl start docker

2. Verify that Docker is installed correctly. To do this step, run the hello-world image::

    # sudo docker run hello-world

After you complete the steps to install Docker for Fedora 26 or Fedora 27, continue with the Quipucords server installation steps in `Installing the Quipucords Server Container Image  <install.html#container>`_.

.. _container:

Installing the Quipucords Server Container Image
------------------------------------------------
After Docker is installed, you can obtain and install the container image that enables the use of the Quipucords server.

1. Download the server container image by entering the following command::

    # curl -k -O -sSL https://github.com/quipucords/quipucords/releases/download/1.0.0/quipucords.1.0.0.tar.gz


2. Load the container image into the local Docker registry with the following command::

    # sudo docker load -i quipucords.1.0.0.tar.gz

The output appears similar to the following example::

    Loaded image: quipucords:1.0.0


3. Verify the image within the local Docker registry by entering the following command::

    # sudo docker images

The output appears similar to the following example::

  REPOSITORY              TAG                 IMAGE ID            CREATED             SIZE
  quipucords              1.0.0               fdadcc4b326f        3 days ago          969MB
