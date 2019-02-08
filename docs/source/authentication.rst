Authentication
--------------
Quipucords uses several different types of authentication models. These include authentication for the interaction between the Quipucords command line interface and the Quipucords server in addition to authentication for the interaction with remote systems during network, vcenter, and satellite scans.

Quipucords Authentication
^^^^^^^^^^^^^^^^^^^^^^^^^
Communication with the Quipucords server uses an authentication token. When you enter the ``qpc server login`` command, you are prompted for the server user name and password. The login command exchanges the user name and password, which are encrypted and transmitted to the server over HTTPS, for the authentication token. The authentication token is then used for all subsequent commands in that session. An authentication token expires when you log out of that session. It also expires on a daily basis.

Network Authentication
^^^^^^^^^^^^^^^^^^^^^^
The Quipucords server inspects the remote systems in a network scan by using the SSH remote connection capabilities of Ansible. The SSH connection can be obtained by using either a user name and password pair or a user name and SSH keyfile pair. If remote systems are accessed with an SSH keyfile, you can also supply a passphrase. Additionally, you can use Quipucords options to elevate privilege to obtain data that requires different privilege levels on the remote system. For more information about authentication that is related to network scans, see `Working with Sources <working_with_sources.html#network>`_.

.. include:: commands.rst

vCenter Server Authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For a vcenter scan, the connectivity and access to the server for vCenter Server derives from basic authentication (user name and password) that is encrypted over HTTPS. If the vCenter Server system that is being accessed does not have a verified SSL certificate from a certificate authority, you can supply the ``ssl-cert-verify False`` option when creating the source. This option disregards the SSL certificate verification during authentication. The vcenter user does not modify any object in vcenter.  Minimal permissions required are read-only access to all objects included in the scan. For more information about authentication that is related to vcenter scans, see `Working with Sources <working_with_sources.html#vcenter>`_.

Satellite Authentication
^^^^^^^^^^^^^^^^^^^^^^^^
For a satellite scan, the connectivity and access to the Satellite server derives from basic authentication (user name and password) that is encrypted over HTTPS. If the Satellite server that is being accessed does not have a verified SSL certificate from a certificate authority, you can supply the ``ssl-cert-verify False`` option when creating the source. This option disregards the SSL certificate verification during authentication. For more information about authentication that is related to satellite scans, see `Working with Sources <working_with_sources.html#satellite>`_.
