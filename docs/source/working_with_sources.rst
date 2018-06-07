Working with Credentials and Sources
------------------------------------
The type of source that you are going to inspect determines the type of data that is required for credential and source configuration. Quipucords currently supports the following source types in the source creation command:

- network
- vcenter
- satellite

A *network* source is composed of one or more host names, one or more IP addresses, IP ranges, or a combination of these network resources. A *vcenter*, for vCenter Server, or *satellite*, for Satellite, source is created with the IP address or host name of that system management solution server.

In addition, the source creation command references one or more credentials. Typically, a network source might include multiple credentials because it is expected that many credentials would be needed to access a broad IP range. Conversely, a vcenter or satellite source would typically use a single credential to access a particular system management solution server.

The following scenarios provide examples of how you would create a network, vcenter, or satellite source and create the credentials required for each.

.. _network:
Creating a Network Source
^^^^^^^^^^^^^^^^^^^^^^^^^
**IMPORTANT:** For a network scan, Quipucords must use the credentials to run some commands with elevated privileges. This access is provided by the use of sudo or similar commands. For more information about this requirement, see `Commands Used in Scans of Remote Network Assets <commands.html>`_

To create a network source, use the following steps:

1. Create at least one network credential with root-level access::

   # qpc cred add --type network --name cred_name --username root_name [--sshkeyfile key_file] [--password]

   If you did not use the ``sshkeyfile`` option to provide an SSH key for the user name value, enter the password of the user with root-level access at the connection password prompt.

   If you want to use SSH keyfiles in the credential, you must copy the keys into the directory that you mapped to ``/sshkeys`` during Quipucords server configuration. In the example information for that procedure, that directory is ``~/quipucords/sshkeys``. The server references these files locally, so refer to the keys as if they are in the ``/sshkeys`` directory from the qpc command.

   For example, for a network credential where the ``/sshkeys`` directory for the server is mapped to ``~/quipucords/sshkeys``, the credential name is ``roothost1``, the user with root-level access is ``root``, and the SSH key for the user is in the ``~/.ssh/id_rsa`` file, you would enter the following commands::

   # cp ~/.ssh/id_rsa ~/quipucords/sshkeys
   # qpc cred add --type network --name roothost1 --username root --sshkeyfile /sshkeys/id_rsa

   Privilege elevation with the ``become-method``, ``become-user``, and ``become-password`` options is also supported to create a network credential for a user to obtain root-level access. You can use the ``become-*`` options with either the ``sshkeyfile`` or the ``password`` option.

   For example, for a network credential where the credential name is ``sudouser1``, the user with root-level access is ``sysadmin``, and the access is obtained through the password option, you would enter the following command::

   # qpc cred add --type network --name sudouser1 --username sysadmin --password --become-password

   After you enter this command, you are prompted to enter two passwords. First, you would enter the connection password for the ``username`` user, and then you would enter the password for the ``become-method``, which is the ``sudo`` command by default.

2. Create at least one network source that specifies one or more network identifiers, such as a host name or host names, an IP address, a list of IP addresses, or an IP range, and one or more network credentials to be used for the scan.

   **TIP:** You can provide IP range values in CIDR or Ansible notation.

   ::

   # qpc source add --type network --name source_name --hosts host_name_or_file --cred cred_name

   For example, for a network source where the source name is ``mynetwork``, the network to be scanned is the ``192.0.2.0/24`` subnet, and the network credentials that are used to run the scan are ``roothost1`` and ``roothost2``, you would enter the following command::

   # qpc source add --type network --name mynetwork --hosts 192.0.2.[1:254] --cred roothost1 roothost2

   You can also use a file to pass in the network identifiers. If you use a file to enter multiple network identifiers, such as multiple individual IP addresses, enter each on a single line. For example, for a network profile where the path to this file is ``/home/user1/hosts_file``, you would enter the following command::

   # qpc source add --type network --name mynetwork --hosts /home/user1/hosts_file --cred roothost1 roothost2

 
   **TIP:** For network sources, you can optionally supply an exclude-hosts field that will omit hosts from a scan.
   ::
   # qpc source add --type network --name mynetwork --hosts 192.0.2.[1:255] --exclude-hosts 192.0.2.255 --cred cred_name

   The ``exclude-hosts`` option supports all of the formatting methods supported by the ``hosts`` option.

.. _vcenter:
Creating a vCenter Source
^^^^^^^^^^^^^^^^^^^^^^^^^
To create a vcenter source, use the following steps:

1. Create at least one vcenter credential::

   # qpc cred add --type vcenter --name cred_name --username vcenter_user --password

   Enter the password of the user with access to vCenter Server at the connection password prompt.

   For example, for a vcenter credential where the credential name is ``vcenter_admin`` and the user with access to the vCenter Server server is ``admin``, you would enter the following command::

   # qpc cred add --type vcenter --name vcenter_admin --username admin --password

2. Create at least one vcenter source that specifies the host name or IP address of the server for vCenter Server and one vcenter credential to be used for the scan::

   # qpc source add --type vcenter --name source_name --hosts host_name --cred cred_name

   For example, for a vcenter source where the source name is ``myvcenter``, the server for the vCenter Server is located at the ``192.0.2.10`` IP address, and the vcenter credential for that server is ``vcenter_admin``, you would enter the following command::

   # qpc source add --type vcenter --name myvcenter --hosts 192.0.2.10 --cred vcenter_admin

   **IMPORTANT:** By default, sources are scanned with full SSL validation, but you might need to adjust the level of SSL validation to connect properly to the server for vCenter Server. The ``source add`` command supports options that are commonly used to downgrade the SSL validation. The ``--ssl-cert-verify`` option can take a value of ``False`` to disable SSL certificate validation; this option would be used for any server with a self-signed certificate. The ``--disable-ssl`` option can take a value of ``True`` to connect to the server over standard HTTP.

.. _satellite:
Creating a Satellite Source
^^^^^^^^^^^^^^^^^^^^^^^^^^^
To create a satellite source, use the following steps:

1. Create at least one satellite credential::

   # qpc cred add --type satellite --name cred_name --username satellite_user --password

   Enter the password of the user with access to the Satellite server at the connection password prompt.

   For example, for a satellite credential where the credential name is ``satellite_admin`` and the user with access is to the Satellite server is ``admin``, you would enter the following command::

   # qpc cred add --type satellite --name satellite_admin --username admin --password

2. Create at least one satellite source that specifies the host name or IP address of the Satellite server, one satellite credential to be used for the scan::

   # qpc source add --type satellite --name source_name --hosts host_name --cred cred_name

   For example, for a satellite source where the source name is ``mysatellite6``, the Satellite server is located at the ``192.0.2.15`` IP address, and the satellite credential for that server is ``satellite_admin``, you would enter the following command::

   # qpc source add --type satellite --name mysatellite6 --hosts 192.0.2.15 --cred satellite_admin

   **IMPORTANT:** By default, sources are scanned with full SSL validation, but you might need to adjust the level of SSL validation to connect properly to the Satellite server. The ``source add`` command supports options that are commonly used to downgrade the SSL validation. The ``--ssl-cert-verify`` option can take a value of ``False`` to disable SSL certificate validation; this option would be used for any server with a self-signed certificate. The Satellite server does not support disabling SSL, so the ``--disable-ssl`` option has no effect.

Editing, Listing, and Clearing Credentials
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In addition to creating credentials for use with sources, you can perform several other operations on credentials. You can edit a credential for situations where passwords or passphrases need to be updated. You can list and filter credentials, and you can remove credentials that are no longer needed. These operations are described in the `Credentials section <man.html#credentials>`_ of the Command Line Usage.


Editing, Listing, and Clearing Sources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In addition to creating sources for use with scans, you can perform several other operations on sources. You can edit a source for situations where credentials need to be updated or options need to be changed. You can list and filter sources, and you can remove sources that are no longer needed. These operations are described in the `Sources section <man.html#sources>`_ of the Command Line Usage.
