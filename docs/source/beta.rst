Beta
====

Installation
------------
Quipucords is delivered via a RPM command line tool and a server container image. Below you will find instructions for installing each of these items.

Command Line
^^^^^^^^^^^^
qpc, the command line tool installed by RPM, is available for `download <https://copr.fedorainfracloud.org/coprs/chambridge/qpc/>`_ from fedora COPR.

1. First, make sure that the EPEL repo is enabled for the server.
You can find the appropriate architecture and version on the `EPEL wiki <https://fedoraproject.org/wiki/EPEL>`_.

Red Hat Enterprise Linux 7::
 rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

Red Hat Enterprise Linux 6::
 rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm

2. Next, add the COPR repo to your server.
You can find the appropriate architecture and version on the `COPR qpc page <https://copr.fedorainfracloud.org/coprs/chambridge/qpc/>`_.

Red Hat Enterprise Linux 7::
 wget -O /etc/yum.repos.d/chambridge-qpc-epel-7.repo https://copr.fedorainfracloud.org/coprs/chambridge/qpc/repo/epel-7/chambridge-qpc-epel-7.repo

Red Hat Enterprise Linux 6::
 wget -O /etc/yum.repos.d/chambridge-qpc-epel-6.repo https://copr.fedorainfracloud.org/coprs/chambridge/qpc/repo/epel-6/chambridge-qpc-epel-6.repo

3. Then, install the qpc beta package (Note the package version below is a placeholder until the beta build is ready).

Red Hat Enterprise Linux 7::
  yum -y install qpc-0.0.1-1.git.227.d622e53.el7.centos

Red Hat Enterprise Linux 6::
  yum -y install qpc-0.0.1-1.git.227.d622e53.el6


Preparing for Server Setup
^^^^^^^^^^^^^^^^^^^^^^^^^^
The Quipucords server is delivered as a container image that will be run on your server. First you must install the necessary dependency, Docker, in order to run the container.

Installing Docker on Red Hat Enterprise Linux 6.6+
""""""""""""""""""""""""""""""""""""""""""""""""""
To run Docker on Red Hat-6.6 or later, you need kernel 2.6.32-431 or higher.

To check your current kernel version, open a terminal and use uname -r to display your kernel version::
  $ uname -r
  3.10.0-229.el7.x86_64

Finally, is it recommended that you fully update your system. Please keep in mind that your system should be fully patched to fix any potential kernel bugs. Any reported kernel bugs may have already been fixed on the latest kernel packages

If your system meets the minimum required kernel version you can proceed with the install of Docker with the following steps:

1. Log into your machine as a user with ``sudo`` or ``root`` privileges.


2. Download the Docker RPM to the current directory::

  $ curl -O -sSL https://yum.dockerproject.org/repo/main/centos/6/Packages/docker-engine-1.7.1-1.el6.x86_64.rpm

3. Use yum to install the package::

  $ sudo yum localinstall --nogpgcheck docker-engine-1.7.1-1.el6.x86_64.rpm

4. Start the Docker daemon::

  $ sudo service docker start

5. Verify that docker is installed correctly by running the hello-world image.::

  $ sudo docker run hello-world
  Unable to find image 'hello-world:latest' locally
  latest: Pulling from hello-world
  a8219747be10: Pull complete
  91c95931e552: Already exists
  hello-world:latest: The image you are pulling has been verified. Important: image verification is a tech preview feature and should not be relied on to provide security.
  Digest: sha256:aa03e5d0d5553b4c3473e89c8619cf79df368babd18681cf5daeb82aab55838d
  Status: Downloaded newer image for hello-world:latest
  Hello from Docker.
  This message shows that your installation appears to be working correctly.


  To generate this message, Docker took the following steps:
   1. The Docker client contacted the Docker daemon.
   2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
          (Assuming it was not already locally available.)
   3. The Docker daemon created a new container from that image which runs the
          executable that produces the output you are currently reading.
   4. The Docker daemon streamed that output to the Docker client, which sent it
          to your terminal.


  To try something more ambitious, you can run an Ubuntu container with:
   $ docker run -it ubuntu bash


  For more examples and ideas, visit:
   http://docs.docker.com/userguide/

6. To ensure Docker starts when you boot your system, do the following::

  $ sudo chkconfig docker on


Installing Docker on Red Hat Enterprise Linux 7
"""""""""""""""""""""""""""""""""""""""""""""""
You can install Docker in different ways, depending on your needs:

- Most users set up Docker’s repositories and install from them, for ease of installation and upgrade tasks. This is the recommended approach.

- Some users download the RPM package and install it manually and manage upgrades completely manually. This is useful in situations such as installing Docker on air-gapped systems with no access to the internet.

**Install using the repository**

1. Log into your machine as a user with ``sudo`` or ``root`` privileges.

2. Install required packages::

  $ sudo yum install -y yum-utils device-mapper-persistent-data lvm2

3. Add repository::

  $ sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

4. Install docker from repository::

  $ sudo yum install docker-ce

**Install from a package**

1. Go to https://download.docker.com/linux/centos/7/x86_64/stable/Packages/ and download the .rpm file for the Docker version you want to install and place it on the intended install system.

2. Log into your machine as a user with ``sudo`` or ``root`` privileges.

3. Install Docker, changing the path below to the path where you downloaded the Docker package::

  $ sudo yum install /path/to/package.rpm

**Start Docker**

Now that Docker has been installed on the system perform the following steps to get running.

1. Start Docker::

  $ sudo systemctl start docker

2. Verify that docker is installed correctly by running the hello-world image::

  $ sudo docker run hello-world


Obtaining the Server Image
^^^^^^^^^^^^^^^^^^^^^^^^^^
Now that Docker has been installed we can obtain the container image that will enable the use of the Quipucords server.

**TBD**


Configuration
-------------

Running the Quipucords Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
With the Quipucords container image now available on your system's image registry we can start the server.

There are several configurable options that must be considered:

- Exposed server port
- Selecting a directory for SSH keys
- Selecting a directory for the SQLlite database
- Selecting a directory for log output


The server exposes port 443, which is the standard HTTPS port. You may choose to utilize that port or re-map the port on your server.

If you selected to expose port 443 then you would use the following option when running the image ``-p443:443``. If you wish to re-map the port on your system Docker's mapping is -p<host_port>:<container_port>. If you choose for example to re-map the port to 8443 the option to supply would be ``-p8443:443``. Additionally, Docker supplies an option to select a free port for all exposed ports by using the ``-P`` option; the port mapping is then available from the ``docker ps`` command.


For the next three configuration options we will take a simple setup strategy for the Quipucords server and create a "home directory" for the server.

1. Create the home directory ``/opt/quipucords``::

  mkdir -p /opt/quipucords

2. Change to that directory::

  cd /opt/quipucords

3. Create directories to house the SSH keys (``/opt/quipucords/sshkeys``), database (``/opt/quipucords/data``), and log output (``/opt/quipucords/log``)::

  mkdir sshkeys
  mkdir data
  mkdir log


Following these steps we can now launch the Quipucords server with the following docker command::

  docker run --name quipucords -d -p443:443 -v /opt/quipucords/sshkeys:/sshkeys -v /opt/quipucords/data:/var/data -v /opt/quipucords/log:/var/log -i quipucords:latest

The above command starts the server running on port ``443`` mapping the server's directories to the home directory we just created. You can view the status of the running server with ``docker ps``.

Verify the server is responding correctly by launching a browser to **https://<ip_address>:<port>/admin**. If your browser is on the same system as the server and you exposed port ``443`` the URL would be **https://localhost/admin**. When your browser loads you should see the administrative login dialog. From here you can log into the server and change the default password. The server comes defaulted with a user **admin** and password **pass**. You should find the "Change Password" selection in the upper right navigation bar.


Configuring the Command Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
With the server up and running you can now configure **qpc** to work with the server. You can do this with the ``qpc server config`` command. The ``qpc server config`` command takes a ``--host <host>`` flag and an optional ``--port <port>`` flag; defaults to ``443``. If you are using qpc on the same system where the server is running you can supply ``--host 127.0.0.1`` otherwise supply the correct IP address. If you decided to remap the port to another port you must supply that to the port option (i.e. ``--port 8443``).

Now the command line has been configured you can log in with the ``qpc server login`` command. Verify your ability to log into the server.
