Step-by-Step Installation
-------------------------
You can install the command line and server components by using the following instructions.

Installing the Ansible Prerequisite
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
`Ansible installation documentation <http://docs.ansible.com/ansible/latest/intro_installation.html#installing-the-control-machine>`_.

.. include:: install_cli.rst

Installing Docker and the Quipucords Server Container Image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The Quipucords server is delivered as a container image that runs on your server. First you must install and start the necessary prerequisite, Docker, to run the container. Then you can obtain and install the Quipucords server container image.

.. include:: install_server_rhel7.rst
.. include:: install_server_centos7.rst
.. include:: install_server_rhel6_centos6.rst
.. include:: install_server_fedora.rst
.. include:: install_container_image.rst
.. include:: configure.rst

Configuring Quipucords
----------------------
When the installation completes, the Quipucords server is installed and started. In addition, a connection to the command line tool is configured on the same system on which the server is installed. However, you must still complete the following steps before you can begin using Quipucords:

- `Changing the Default Password for the Quipucords Server <install.html#change-default-pw>`_
- `Logging in to the Quipucords Server <cli_server_interaction.html#login>`_
