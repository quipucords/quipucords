Installing Docker on Red Hat Enterprise Linux 7
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can install Docker from the RHEL extras repository:

- You can set up the the `Extras <https://access.redhat.com/solutions/912213>`_ ( ``rhel-7-server-extras-rpms`` ) and `Optional <https://access.redhat.com/solutions/265523>`_ ( ``rhel-7-server-optional-rpms`` ) repositories and then install Docker from them. This is the recommended approach because it simplifies the installation and upgrade tasks. Visit the Red Hat `documentation <https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_atomic_host/7/html-single/getting_started_with_containers/index#getting_docker_in_rhel_7>`_ for further detail.

Installing from the repository
""""""""""""""""""""""""""""""
1. Make sure that you are logged in as a user with ``sudo`` or ``root`` privileges.

2. Enable the required repositories::

    # sudo subscription-manager repos --enable=rhel-7-server-rpms
    # sudo subscription-manager repos --enable=rhel-7-server-extras-rpms
    # sudo subscription-manager repos --enable=rhel-7-server-optional-rpms

3. Install Docker from the repository::

    # sudo yum install docker device-mapper-libs device-mapper-event-libs


Starting Docker on Red Hat Enterprise Linux 7
"""""""""""""""""""""""""""""""""""""""""""""
After you install Docker, you must start it and verify that it is running.

1. Start Docker::

    # sudo systemctl start docker

2. Verify that Docker is installed correctly. To do this step, run the hello-world image::

    # sudo docker run hello-world

After you complete the steps to install Docker for Red Hat Enterprise Linux 7, continue with the Quipucords server installation steps in `Installing the Quipucords Server Container Image <install.html#container>`_.
