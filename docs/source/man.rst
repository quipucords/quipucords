qpc
===

Name
----

qpc - Inspect and report on product entitlement metadata from various sources, including networks and systems management solutions.


Synopsis
--------

``qpc command subcommand [options]``

Description
-----------

Quipucords, accessed through the ``qpc`` command, is an inspection and reporting tool to identify environment data, or *facts*, such as the number of physical and virtual systems on a network, their operating systems and other configuration data, and versions of some key packages and products for almost any Linux or UNIX version. The ability to inspect the software and systems that are running on your network improves your ability to understand and report on your entitlement usage. Ultimately, this inspection and reporting process is part of the larger system administration task of managing your inventories.

Quipucords uses two types of configuration to manage the inspection process. A *credential* contains configuration such as the username and password or SSH key of the user that runs the inspection process.  A *source* defines the entity to be inspected, such as a host, subnet, network, or systems management solution such as vCenter Server or Satellite, plus includes one or more credentials to use to access that network or systems management solution during the inspection process. You can save multiple credentials and sources to use with Quipucords in various combinations as you run inspection processes, or *scans*. When you have completed a scan, you can access the output as a *report* to review the results.

By default, the credentials and sources that are created when using Quipucords are encrypted in a database. The values are encrypted with AES-256 encryption. They are decrypted when the Quipucords server runs a scan, by using a *vault password* to access the encrypted values that are stored in the database.

Quipucords is an *agentless* inspection tool, so there is no need to install the tool on multiple systems. Inspection for the entire network is centralized on a single machine.

This man page describes the commands, subcommands, and options for the ``qpc`` command and includes usage information and example commands.

Usage
-----

``qpc`` performs five major tasks:

* Logging in to the server:

  ``qpc server login --username admin``

* Creating credentials:

  ``qpc cred add --name=credname1 --type=type --username=user1 --password``

* Creating sources:

  ``qpc source add --name=sourcename1 --type=type --hosts server1.example.com server2.example.com --cred credname1 credname2``

* Running a scan:

  ``qpc scan start --sources sourcename1``

* Working with scans:

  ``qpc scan show --id=X``

The following sections describe these commands, their subcommands, and their options in more detail.

Server Authentication
---------------------

Use the ``qpc server`` command to configure connectivity with the server and to log in to and log out of the server.

Configuring the server
~~~~~~~~~~~~~~~~~~~~~~

To configure the connection to the server, supply the host address. Supplying a port for the connection is optional.

**qpc server config --host=** *host* **[--port=** *port* **]**

``--host=host``

  Required. Sets the host address for the server. If you are running the ``qpc`` command on the same system as the server, the default host address for the server is ``127.0.0.1``.

``--port=port``

  Optional. Sets the port to use to connect to the server. The default is ``8000``.


Logging in to the server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To log in to the server after the connection is configured, use the ``login`` subcommand. This command retrieves a token that is used for authentication with subsequent command line interface commands.

**qpc server login [--username=** *username* **]**

``--username=username``

  Optional. Sets the username that is used to log in to the server.


Logging out of the server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To log out of the server, use the ``logout`` subcommand. This command removes the token that was created when the ``login`` command was used.

**qpc server logout**


Credentials
-----------

Use the ``qpc cred`` command to create and manage credentials.

A credential defines a set of user authentication information to be used during a scan. A credential includes a username and a password or SSH key. Quipucords uses SSH to connect to servers on the network and uses credentials to access those servers.

When a scan runs, it uses a source that contains information such as the host names, IP addresses, a network, or a systems management solution to be accessed. The source also contains references to the credentials that are required to access those systems. A single source can contain a reference to multiple credentials as needed to connect to all systems in that network or systems management solution.

Creating and Editing Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a credential, supply the type of credential and supply SSH credentials as either a username-password pair or a username-key pair. Quipucords stores each set of credentials in a separate credential entry.

**qpc cred add --name=** *name* **--type=** *(network | vcenter | satellite)* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **--become-method=** *(sudo | su | pbrun | pfexec | doas | dzdo | ksu | runas )* **--become-user=** *user* **[--become-password]**

``--name=name``

  Required. Sets the name of the new credential. For the value, use a descriptive name that is meaningful to your organization. For example, you could identify the user or server that the credential relates to, such as ``admin12`` or ``server1_jdoe``. Do not include the password as part of this value, because the value for the ``--name`` option might be logged or printed during ``qpc`` execution.

``--type=type``

  Required. Sets the type of credential. The value must be ``network``, ``vcenter``, or ``satellite``. The type cannot be edited after a credential is created.

``--username=username``

  Required. Sets the username of the SSH identity that is used to bind to the server.

``--password``

  Prompts for the password for the ``--username`` identity. Mutually exclusive with the ``--sshkeyfile`` option.

``--sshkeyfile=key_file``

  Sets the path of the file that contains the private SSH key for the ``--username`` identity. Mutually exclusive with the ``--password`` option.

``--sshpassphrase``

  Prompts for the passphrase to be used when connecting with an SSH keyfile that requires a passphrase. Can only be used with the ``--sshkeyfile`` option.

``--become-method=become_method``

  Sets the method to become for privilege escalation when running a network scan. The value must be ``sudo``, ``su``, ``pbrun``, ``pfexec``, ``doas``, ``dzdo``, ``ksu``, or ``runas``. The default is set to ``sudo`` when the credential type is ``network``.

``--become-user=user``

  Sets the user to become when running a privileged command during network scan.

``--become-password``

  Prompts for the privilege escalation password to be used when running a network scan.

The information in a credential, such as a password, become password, SSH keys, the become_method, or even the username, might change. For example, network security might require passwords to be updated every few months. Use the ``qpc cred edit`` command to change credential information. The parameters for ``qpc cred edit`` are the same as those for ``qpc cred add``.

**qpc cred edit --name=** *name* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **--become-method=** *(sudo | su | pbrun | pfexec | doas | dzdo | ksu | runas )* **--become-user=** *user* **[--become-password]**

Listing and Showing Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc cred list`` command returns the details for every credential that is configured for Quipucords. This output includes the name, username, password, SSH keyfile, and sudo password for each entry. Passwords are masked if provided, if not, they will appear as ``null``.

**qpc cred list --type=** *(network | vcenter | satellite)*

``--type=type``

  Optional.  Filters the results by credential type.  The value must be ``network``, ``vcenter``, or ``satellite``.

The ``qpc cred show`` command is the same as the ``qpc cred list`` command, except that it returns details for a single specified credential.

**qpc cred show --name=** *name*

``--name=name``

  Required. Contains the name of the credential entry to display.


Clearing Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some credentials. Use the ``clear`` subcommand to delete credentials.

**IMPORTANT:** Remove or change the credential from any source that uses it *before* clearing a credential. Otherwise, any attempt to use the source to run a scan runs the command with a nonexistent credential, an action that causes the ``qpc`` command to fail.

**qpc cred clear (--name** *name* **| --all)**

``--name=name``

  Contains the credential to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all credentials. Mutually exclusive with the ``--name`` option.


Sources
----------------

Use the ``qpc source`` command to create and manage sources.

A source defines a collection of network information, including IP addresses or host names, or systems management solution information, in addition to SSH ports and SSH credentials. The SSH credentials are provided through reference to one or more credentials. A scan can reference a source so that the act of running the scan is automatic and repeatable, without a requirement to reenter network information for each scan attempt.

Creating and Editing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a source, supply the type of source with the ``type`` option, one or more host names or IP addresses to connect to with the ``--hosts`` option, and the credentials needed to access those systems with the ``--cred`` option. The ``qpc source`` command allows multiple entries for the ``hosts`` and ``cred`` options. Therefore, a single source can access a collection of servers and subnets as needed to create an accurate and complete scan.

**qpc source add --name=** *name*  **--type=** *(network | vcenter | satellite)* **--hosts** *ip_address* **--cred** *credential* **[--port=** *port* **]**

``--name=name``

  Required. Sets the name of the new source. For the value, use a descriptive name that is meaningful to your organization, such as ``APSubnet`` or ``Lab3``.

``--type=type``

  Required. Sets the type of source.  The value must be ``network``, ``vcenter``, or ``satellite``. The type cannot be edited after a source is created.

``--hosts ip_address``

  Sets the host name, IP address, or IP address range to use when running a scan. You can also provide a path for a file that contains a list of host names or IP addresses or ranges, where each item is on a separate line. The following examples show several different formats that are allowed as values for the ``--hosts`` option:

  * A specific host name:

    --hosts server.example.com

  * A specific IP address:

    --hosts 192.0.2.19

  * An IP address range, only valid for the ``network`` type:

    --hosts 192.0.2.[0:255]
    or
    --hosts 192.0.2.0/24

  * A file:

    --hosts /home/user1/hosts_file

``--cred credential``

  Contains the name of the credential to use to authenticate to the systems that are being scanned. If the individual systems that are being scanned each require different authentication credentials, you can use more than one credential. To add multiple credentials to the source, separate each value with a space, for example:

  ``--cred first_auth second_auth``

  **IMPORTANT:** A credential must exist before you attempt to use it in a source. A credential must be of the same type as the source.

``--port=port``

  Optional. Sets a port to be used for the scan. This value supports connection and inspection on a non-standard port. By default, a network scan runs on port 22 and a vcenter or satellite scan runs on port 443.

The information in a source might change as the structure of the network changes. Use the ``qpc source edit`` command to edit a source to accommodate those changes.

Although ``qpc source`` options can accept more than one value, the ``qpc source edit`` command is not additive. To edit a source and add a new value for an option, you must enter both the current and the new values for that option. Include only the options that you want to change in the ``qpc source edit`` command. Options that are not included are not changed.

**qpc source edit --name** *name* **[--hosts** *ip_address* **] [--cred** *credential* **] [--port=** *port* **]**

For example, if a source contains a value of ``server1creds`` for the ``--cred`` option, and you want to change that source to use both the ``server1creds`` and ``server2creds`` credentials, you would edit the source as follows:

``qpc source edit --name=mysource --cred server1creds server2creds``

**TIP:** After editing a source, use the ``qpc source show`` command to review those edits.

Listing and Showing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc source list`` command returns the details for all configured sources. The output of this command includes the host names, IP addresses, or IP ranges, the credentials, and the ports that are configured for each source.

**qpc source list [--type=** *(network | vcenter | satellite)* **]**

``--type=type``

  Optional.  Filters the results by source type. The value must be ``network``, ``vcenter``, or ``satellite``.


The ``qpc source show`` command is the same as the ``qpc source list`` command, except that it returns details for a single specified source.

**qpc source show --name=** *source*

``--name=source``

  Required. Contains the source to display.


Clearing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some sources. Use the ``qpc source clear`` command to delete sources.

**qpc source clear (--name=** *name* **| --all)**

``--name=name``

  Contains the name of the source to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored sources. Mutually exclusive with the ``--name`` option.


Scanning
--------

Use the ``qpc scan start`` command to run scans on one or more sources. This command scans all of the host names or IP addresses that are defined in the supplied sources. Each instance of a scan is assigned a unique *identifier* to identify the scan results, so that the results data can be viewed later.

**IMPORTANT:** If any ssh-agent connection is set up for a target host, that connection will be used as a fallback connection.

**qpc scan start --sources=** *source_list* **[--max-concurrency=** *concurrency* **]** **--disable-optional-products=** *products_list*

``--sources=source_list``

  Required. Contains the list of source names to use to run the scan.

``--max-concurrency=concurrency``

  Contains the maximum number of parallel system scans. If this value is not provided, the default is ``50``.

``--disable-optional-products=products_list``

  The product inspection exclusion. Contains the list of products to exclude from inspection. Valid values are jboss_eap, jboss_fuse, and jboss_brms.

Listing and Showing Scans
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc scan list`` command returns the summary details for all executed scans. The output of this command includes the identifier, the source or sources, and the current state of the scan.

**qpc scan list** **--type=** *(connect | inspect)* **--state=** *(created | pending | running | paused | canceled | completed | failed)*

``--type=type``

  Optional. Filters the results by scan type. This value must be ``connect`` or ``inspect``. A scan of type ``connect`` is a scan that began the process of connecting to the defined systems in the sources, but did not transition into inspecting the contents of those systems. A scan of type ``inspect`` is a scan that moves into the inspection process.

``--state=state``

  Optional. Filters the results by scan state. This value must be ``created``, ``pending``, ``running``, ``paused``, ``canceled``, ``completed``, or ``failed``.

The ``qpc scan show`` command is the same as the ``qpc scan list`` command, except that it returns summary details for a single specified scan. You can also use this command to display the results of a scan.

**qpc scan show --id=** *scan_identifier* **[--results]**

``--id=scan_identifier``

  Required. Contains the scan identifier to display.

``--results``

  Optional. Displays the results of the scan instead of the status. The results are the raw output of the scan before that output is consolidated into a report. Because the results can include many lines of data, you might want to redirect the output of this command to a file if you use the ``--results`` option.

Controlling Scans
~~~~~~~~~~~~~~~~~

When scans are queued and running, you might need to control the execution of scans due to the needs of other business processes in your organization. The ``pause``, ``restart``, and ``cancel`` subcommands enable you to control scan execution.

The ``qpc scan pause`` command halts the execution of a scan, but enables it to be restarted at a later time.

**qpc scan pause --id=** *scan_identifier*

``--id=scan_identifier``

  Required. Contains the identifier of the scan to pause.


The ``qpc scan restart`` command restarts the execution of a scan that is paused.

**qpc scan restart --id=** *scan_identifier*

``--id=scan_identifier``

  Required. Contains the identifier of the scan to restart.


The ``qpc scan cancel`` command cancels the execution of a scan. A canceled scan cannot be restarted.

**qpc scan cancel --id=** *scan_identifier*

``--id=scan_identifier``

  Required. Contains the identifier of the scan to cancel.


Options for All Commands
------------------------

The following options are available for every Quipucords command.

``--help``

  Prints the help for the ``qpc`` command or subcommand.

``-v``

  Enables the verbose mode. The ``-vvv`` option increases verbosity to show more information. The ``-vvvv`` option enables connection debugging.

Examples
--------

Creating a new network type credential with a keyfile
  ``qpc cred add --name=new_creds --type=network --username=qpc_user --sshkeyfile=/etc/ssh/ssh_host_rsa_key``
Creating a new network type credential with a password
  ``qpc cred add --name=other_creds --type=network --username=qpc_user_pass --password``
Creating a new vcenter type credential
  ``qpc cred add --name=vcenter_cred --type=vcenter --username=vc-user_pass --password``
Creating a new network source
  ``qpc source add --name=new_source --type network --hosts 1.192.0.19 1.192.0.20 --cred new_creds``
Creating a new vcenter source
  ``qpc source add --name=new_source --type vcenter --hosts 1.192.0.19 --cred vcenter_cred``
Editing a source
  ``qpc source edit --name=new_source --hosts 1.192.0.[0:255] --cred new_creds other_creds``
Running a scan with one source
  ``qpc scan start --sources new_source``

Security Considerations
-----------------------

The authentication data in the credentials and the network-specific and system-specific data in sources are stored in an AES-256 encrypted value within a database. A vault password is used to encrpyt and decrypt values. The vault password and decrypted values are in the system memory, and could theoretically be written to disk if memory swapping is enabled.

Authors
-------

Quipucords was originally written by Chris Hambridge <chambrid@redhat.com>, Noah Lavine <nlavine@redhat.com>, and Kevan Holdaway <kholdawa@redhat.com>.

Copyright
---------

Copyright 2018 Red Hat, Inc. Licensed under the GNU Public License version 3.
