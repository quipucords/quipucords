Installing Quipucords
=====================
Quipucords is delivered in two parts, a command line tool as an RPM package and a server as a container image. The following instructions describe how to install the parts of Quipucords.

Installing the Quipucords Command Line Tool
-------------------------------------------
qpc, the command line tool that is installed by RPM, is available for `download <https://copr.fedorainfracloud.org/coprs/chambridge/qpc/>`_ from the Fedora COPR build and repository system.

1. Enable the EPEL repo for the server. You can find the appropriate architecture and version on the `EPEL wiki <https://fedoraproject.org/wiki/EPEL>`_.

  - For Red Hat Enterprise Linux 7, enter the following command::

    # rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

  - For Red Hat Enterprise Linux 6, enter the following command::

    # rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm

2. Add the COPR repo to your server. You can find the appropriate architecture and version on the `COPR qpc page <https://copr.fedorainfracloud.org/coprs/chambridge/qpc/>`_.


  - For Red Hat Enterprise Linux 7, enter the following command:

  ::

   # wget -O /etc/yum.repos.d/chambridge-qpc-epel-7.repo https://copr.fedorainfracloud.org/coprs/chambridge/qpc/repo/epel-7/chambridge-qpc-epel-7.repo

  - For Red Hat Enterprise Linux 6, enter the following command:

  ::

    # wget -O /etc/yum.repos.d/chambridge-qpc-epel-6.repo https://copr.fedorainfracloud.org/coprs/chambridge/qpc/repo/epel-6/chambridge-qpc-epel-6.repo

3. Install the qpc beta package:

  - For Red Hat Enterprise Linux 7, enter the following command:
    ``# yum -y install qpc``

  - For Red Hat Enterprise Linux 6, enter the following command:
    ``# yum -y install qpc``

Installing the Quipucords Server Requirement and Container Image
----------------------------------------------------------------
The Quipucords server is delivered as a container image that runs on your server. First you must install and start the necessary prerequisite, Docker, to run the container. Then you can obtain and install the Quipucords server container image.

Installing the Docker Prerequisite
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The instructions for installing Docker vary according to your system configuration.

Installing Docker on Red Hat Enterprise Linux 7
"""""""""""""""""""""""""""""""""""""""""""""""
You can install Docker in different ways, depending on your needs:

- You can set up the Docker repositories and then install from them. This choice is the recommended approach because it simplifies the installation and upgrade tasks.

- You can download the RPM package, install it manually, and manage upgrades manually. This choice is useful when Docker is installed on air-gapped systems that have no access to the internet.

Installing from the repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

2. Install the required packages:

  ``# sudo yum install -y yum-utils device-mapper-persistent-data lvm2``

3. Add the repository:

  ``# sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo``

4. Install Docker from the repository:

  ``# sudo yum install docker-ce``

Installing from a package
~~~~~~~~~~~~~~~~~~~~~~~~~
1. Go to https://download.docker.com/linux/centos/7/x86_64/stable/Packages/. For the Docker version that you want to install, download the RPM package to the intended installation system.

2. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

3. Install Docker, changing the path in the following example to the path where you downloaded the Docker package:

 ``# sudo yum install /path/to/package.rpm``

Starting Docker on Red Hat Enterprise Linux 7
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After you install Docker, you must start it and verify that it is running.

1. Start Docker:

  ``# sudo systemctl start docker``

2. Verify that Docker is installed correctly. To do this step, run the hello-world image:

  ``# sudo docker run hello-world``

After you complete the steps to install Docker for Red Hat Enterprise Linux 7 or later, you can continue with the steps to obtain the Quipucords server container image.

Installing Docker on Red Hat Enterprise Linux 6.6 or later
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
To install Docker on Red Hat Enterprise Linux 6.6 or later, you must have kernel 2.6.32-431 or later installed.

To check the current kernel release, open a terminal session and use the ``uname`` command to display the kernel release information, as shown in the following example::

  # uname -r

The output of this command is similar to the following example::

  2.6.32-573.el6.x86_64

**TIP:** After you confirm that you have at least the minimum required kernel release, it is recommended that you fully update your system. Having a fully patched system can help you avoid kernel bugs that have already been fixed on the latest kernel packages.

When your system meets the minimum required kernel release, you can use the following steps to install Docker:

1. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

2. Download the Docker RPM package to the current directory:

  ``# curl -k -O -sSL https://yum.dockerproject.org/repo/main/centos/6/Packages/docker-engine-1.7.1-1.el6.x86_64.rpm``

3. Install the Docker package with yum:

  ``# sudo yum localinstall --nogpgcheck docker-engine-1.7.1-1.el6.x86_64.rpm``

Starting Docker on Red Hat Enterprise Linux 6.6 or later
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
After you install Docker, you must start it and verify that it is running.

1. Start the Docker daemon:

  ``# sudo service docker start``

2. Verify that Docker is installed correctly. To do this step, run the hello-world image:

  ``# sudo docker run hello-world``

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


3. To ensure that Docker starts when you start your system, enter the following command:

  ``# sudo chkconfig docker on``

After you complete the steps to install Docker for Red Hat Enterprise Linux 6.6 or later, you can continue with the steps to obtain the Quipucords server container image.

Installing the Quipucords Server Container Image
------------------------------------------------
After Docker is installed, you can obtain and install the container image that enables the use of the Quipucords server.

Start by downloading the server container image from the provided URL::

  #  curl -k -O -sSL https://ftp.redhat.com/repo/container/quipucords.1.0.0.tar.gz


Load the container image into the local Docker registry with the following command::

  #  sudo docker load -i quipucords.1.0.0.tar.gz
  ...
  Loaded image: quipucords:1.0.0


You can verify the image within the local Docker registry::

  #  sudo docker images
  REPOSITORY              TAG                 IMAGE ID            CREATED             SIZE
  quipucords              1.0.0               fdadcc4b326f        3 days ago          969MB
