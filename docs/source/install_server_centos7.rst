Installing Docker on CentOS 7
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can install Docker in different ways, depending on your needs:

- You can set up the Docker repositories and then install from them. This choice is the recommended approach because it simplifies the installation and upgrade tasks.

- You can download the RPM package, install it manually, and manage upgrades manually. This choice is useful when Docker is installed on systems with limited or no access to the internet.

Installing from the repository
++++++++++++++++++++++++++++++

To install from the repository, use the following steps:

1. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

2. Install the required packages::

    # sudo yum install -y yum-utils device-mapper-persistent-data lvm2

3. Add the repository::

    # sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

4. Install Docker from the repository::

    # sudo yum install docker-ce

Installing from a package
+++++++++++++++++++++++++

To install from a package, use the following steps:

1. Go to https://download.docker.com/linux/centos/7/x86_64/stable/Packages/. For the Docker version that you want to install, download the RPM package to the intended installation system.

2. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

3. Install Docker, changing the path in the following example to the path where you downloaded the Docker package::

    # sudo yum install /path/to/package.rpm

Starting Docker on CentOS 7
+++++++++++++++++++++++++++

After you install Docker, you must start it and verify that it is running.

1. Start Docker::

    # sudo systemctl start docker

2. Verify that Docker is installed correctly. To do this step, run the hello-world image::

    # sudo docker run hello-world

After you complete the steps to install Docker for CentOS 7, continue with the Quipucords server installation steps in `Installing the Quipucords Server Container Image <install.html#container>`_.
