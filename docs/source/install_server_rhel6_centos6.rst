Installing Docker on Red Hat Enterprise Linux and CentOS 6.6 or later
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To install Docker on Red Hat Enterprise Linux or CentOS 6.6 or later, you must have kernel 2.6.32-431 or later installed.

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

Starting Docker on Red Hat Enterprise Linux and CentOS 6.6 or later
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

After you complete the steps to install Docker for Red Hat Enterprise Linux 6.6 or later or CentOS 6.6 or later, you can continue with the Quipucords server installation steps in `Installing the Quipucords Server Container Image <install.html#container>`_.
