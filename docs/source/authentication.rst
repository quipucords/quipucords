Authentication
--------------
This section breaks down the different authentication models used within Quipucords from interacting with the server from the command line or how the server interacts with remote systems.

Quipucords Authentication
^^^^^^^^^^^^^^^^^^^^^^^^^
Communication with the Quipucords server utilizes an authentication token. From the command line a user obtains an authentication token with the ``qpc server login`` command. The login command exchanges the username and password, which are encrypted and transmitted to the server over HTTPS, for an authentication token. An authentication token expires on a daily basis.

Network Authentication
^^^^^^^^^^^^^^^^^^^^^^
The Quipucords server inspects remote systems utilizing `Ansible <https://www.ansible.com/>`_ to make an SSH connection. The SSH connection can be obtained using a username and password or username and SSH keyfile. If accessed with an SSH keyfile you can also supply a passphrase. Additionally, you can supply the ability to escalate privilege to obtain data that requires different privilege levels on the remote sytem. See the network section within `Working with Sources <working_with_sources.html#network>`_ for more details.

vCenter Server Authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Connectivity and access to the vCenter Server utilizes basic authentication (username and password) encrypted over HTTPS. If the vCenter Server being accessed does not have a verified SSL certificate from a certificate authority you can supply the ``ssl-cert-verify False`` option when creating the source to disregard the SSL certificate verification during authentication. See the vCenter server section within `Working with Sources <working_with_sources.html#vcenter>`_ for more details.

Satellite Authentication
^^^^^^^^^^^^^^^^^^^^^^^^
Connectivity and access to the Satellite utilizes basic authentication (username and password) encrypted over HTTPS. If the Satellite being accessed does not have a verified SSL certificate from a certificate authority you can supply the ``ssl-cert-verify False`` option when creating the source to disregard the SSL certificate verification during authentication.See the Satellite section within `Working with Sources <working_with_sources.html#satellite>`_ for more details.
