.. _commandline:

Installing the Quipucords Command Line Tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
qpc, the command line tool that is installed by RPM, is available for `download <https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/>`_ from the Fedora COPR build and repository system. Use the following steps to install the command line tool.

1. Enable the EPEL repo for the server. You can find the appropriate architecture and version on the `EPEL wiki <https://fedoraproject.org/wiki/EPEL>`_.

  - For Red Hat Enterprise Linux 7 or CentOS 7, enter the following command::

      # rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

  - For Red Hat Enterprise Linux 6 or CentOS 6, enter the following command::

      # rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm

2. Add the COPR repo to your server. You can find the appropriate architecture and version on the `COPR qpc page <https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/>`_.


  - For Red Hat Enterprise Linux 7 or CentOS 7, enter the following command::

      # wget -O /etc/yum.repos.d/group_quipucords-qpc-epel-7.repo https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/repo/epel-7/group_quipucords-qpc-epel-7.repo

  - For Red Hat Enterprise Linux 6 or CentOS 6, enter the following command::

      # wget -O /etc/yum.repos.d/group_quipucords-qpc-epel-6.repo https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/repo/epel-6/group_quipucords-qpc-epel-6.repo

  - For Fedora 27, enter the following command::

      # wget -O /etc/yum.repos.d/group_quipucords-qpc-fedora-27.repo https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/repo/fedora-27/group_quipucords-qpc-fedora-27.repo

  - For Fedora 26, enter the following command::

      # wget -O /etc/yum.repos.d/group_quipucords-qpc-fedora-26.repo https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/repo/fedora-26/group_quipucords-qpc-fedora-26.repo

3. Install the qpc package:

  - For Red Hat Enterprise Linux 7 or CentOS 7, enter the following command::

      # yum -y install qpc-0.0.42-1.git.669.98244b2.el7.centos

  - For Red Hat Enterprise Linux 6 or CentOS 6, enter the following command::

      # yum -y install qpc-0.0.42-1.git.669.98244b2.el6

  - For Fedora 27, enter the following command::

      # yum -y install qpc-0.0.42-1.git.669.98244b2.fc27

  - For Fedora 26, enter the following command::

      # yum -y install qpc-0.0.42-1.git.669.98244b2.fc26
