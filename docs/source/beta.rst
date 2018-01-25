Quipucords Beta
===============

Installation
------------
quipucords is delivered via a RPM command line tool and a server container image. Below you will find instructions for installing each of these items.

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
