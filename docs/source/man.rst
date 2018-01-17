qpc
===

Name
----

qpc - Discover and manage product entitlement metadata from various sources.


Synopsis
--------

``qpc command subcommand [options]``

Description
-----------

Quipucords, and the ``qpc`` command, is a discovery and inspection tool to identify environment data, or *facts*, such as the number of physical and virtual systems on a network, their operating systems and other configuration data, and versions of some key packages and products for almost any Linux or UNIX version. The ability to discover and inspect the software and systems that are running on the network improves your ability to understand and report on your entitlement usage. Ultimately, this discovery and inspection process is part of the larger system administration task of managing your inventories.

Quipucords uses two types of configuration to manage the discovery and inspection process. A *credential* contains configuration such as the username and password or SSH key of the user that runs the discovery and inspection process.  A *source* defines the network, such as a host, subnet, or network that is being monitored, plus includes one or more credentials to use to access that network during the discovery and inspection process. You can save multiple credentials and sources to use with Quipucords in various combinations as you run discovery and inspection processes, or *scans*.

By default, the credentials and sources that are created when using Quipucords are encrypted in a database. The values are encrypted with AES-256 encryption and are decrypted when the Quipucords server executes a scan, by using a *vault password* to access the encrypted values stored in the database.

Quipucords is an *agentless* discovery and inspection tool, so there is no need to install the tool on multiple systems. Discovery and inspection for the entire network is centralized on a single machine.

This man page describes the commands, subcommands, and options for the ``qpc`` command and includes basic usage information. For more detailed information and examples, including best practices, see the Quipucords README file.

Usage
-----

``qpc`` performs four major tasks:

* Server login:

  ``qpc server login --username admin``

* Creating credentials:

  ``qpc cred add ...``

* Creating sources:

  ``qpc source add --type TYPE --name=X --hosts X Y Z --cred A B``

* Running a scan:

  ``qpc scan start --sources X``

* Working with scans:

  ``qpc scan show --id=X``

The following sections describe these commands, their subcommands, and their options in more detail.

Server Authentication
---------------------

Use the ``qpc server`` command to configure connectivity and login and logout of the server.

Configuring the server
~~~~~~~~~~~~~~~~~~~~~~

To configure connection to the server supply the host address and optionally the port.

**qpc server config --host=** *host* **[--port=** *port* **]**

``--host=host``

  Required. Sets the host address for the server. If running QPC on the same system as the server you can use "127.0.0.1".

``--port=port``

  Optional. Sets the port to connect to the server on, defaulting to 8000.


Authentication with the server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To log in to the server after the connection has been configured use the login subcommand.

**qpc server login [--username=** *username* **]**

``--username=username``

  Optional. Sets the username used to authenticate with the server.


This command retrieves a token used for authentication for subsequent CLI commands.

Log out of the server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To log out of the server use the logout subcommand.

**qpc server logout***

This command removes the token used for authentication for subsequent CLI commands.


Credentials
-----------

Use the ``qpc cred`` command to create and manage credentials.

A credential defines a set of user authentication configuration to be used during a scan. These user credentials include a username and a password or SSH key. Quipucords uses SSH to connect to servers on the network and uses credentials to access those servers.

When a scan runs, it uses a source that contains the host names or IP addresses to be accessed. The source also contains references to the credentials that are required to access those systems. A single source can contain a reference to multiple credentials as needed to connect to all systems in that network.

Creating and Editing Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a credential, supply SSH credentials as either a username-password pair or a username-key pair. Quipucords stores each set of credentials in a separate credential entry.

**qpc cred add --name=** *name* **--type=** *(network | vcenter | satellite)* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **[--sudo-password]**

``--name=name``

  Required. Sets the name of the new credential. For the value, use a descriptive name that is meaningful to your organization. For example, you could identify the user or server that the credential relates to, such as ``admin12`` or ``server1_jdoe``. Do not include the password as part of this value, because the value for the ``--name`` option might be logged or printed during ``qpc`` execution.

``--username=username``

  Required. Sets the username of the SSH identity that is used to bind to the server.

``--type=type``

  Required. Sets the type of credential.  Must be ``network``, ``vcenter`` or ``satellite``.

``--password``

  Prompts for the password for the ``--username`` identity. Mutually exclusive with the ``--sshkeyfile`` option.

``--sshkeyfile=key_file``

  Sets the path of the file that contains the private SSH key for the ``--username`` identity. Mutually exclusive with the ``--password`` option.

``--sshpassphrase``

  Prompts for the passphrase to be used when connecting using an ssh keyfile that requires a passphrase. Can only be used with the ``--sshkeyfile`` option.

``--sudo-password``

  Prompts for the password to be used when running a command that uses sudo on the systems to be scanned.


The information in a credential, such as a password, sudo password, SSH keys, or even the username, might change. For example, network security might require passwords to be updated every few months. Use the ``qpc cred edit`` command to change the SSH credential information in a credential. The parameters for ``qpc cred edit`` are the same as those for ``qpc cred add``.

**qpc cred edit --name=** *name* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **[--sudo-password]**

Listing and Showing Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc cred list`` command returns the details for every credential that is configured for Quipucords. This output includes the name, username, password, SSH keyfile and sudo password for each entry. Passwords are masked if provided, if not, they will appear as ``null``.

**qpc cred list **--type=** *(network | vcenter | satellite)* **

``--type=type``

  Optional.  Filter list results by credential type.  Must be ``network``, ``vcenter``, or ``satellite``.

The ``qpc cred show`` command is the same as the ``qpc cred list`` command, except that it returns details for a single specified credential.

**qpc cred show --name=** *name*

``--name=name``

  Required. Contains the credential entry to display.


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

A source defines a collection of network information, including IP addresses or host names, SSH ports, and SSH credentials. The SSH credentials are provided through reference to one or more credentials. A discovery and inspection scan can reference a source so that the act of running the scan is automatic and repeatable, without a requirement to reenter network information for each scan attempt.

Creating and Editing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a source, supply one or more host names or IP addresses to connect to with the ``--hosts`` option and the credentials needed to access those systems with the ``--cred`` option. The ``qpc source`` command allows multiple entries for each of these options. Therefore, a single source can access a collection of servers and subnets as needed to create an accurate and complete scan.

**qpc source add --name=** *name*  **--type=** *(network | vcenter | satellite)* **--hosts** *ip_address* **--cred** *credential* **[--port=** *port* **]**

``--name=name``

  Required. Sets the name of the new source. For the value, use a descriptive name that is meaningful to your organization, such as ``APSubnet`` or ``Lab3``.

``--type=type``

  Required. Sets the type of source.  Must be ``network``, ``vcenter``, or ``satellite``.

``--hosts ip_address``

  Sets the host name, IP address, or IP address range to use when running a scan. You can also provide a path for a file that contains a list of host names or IP addresses or ranges, where each item is on a separate line. The following examples show several different formats that are allowed as values for the ``--hosts`` option:

  * A specific host name:

    --hosts server.example.com

  * A specific IP address:

    --hosts 192.0.2.19

  * An IP address range, only valid for network type:

    --hosts 192.0.2.[0:255]
    or
    --hosts 192.0.2.0/24

  * A file:

    --hosts /home/user1/hosts_file

``--cred credential``

  Contains the name of the credential to use to authenticate to the systems that are being scanned. If the individual systems that are being scanned each require different authentication credentials, you can use more than one credential. To add multiple credentials to the source, separate each value with a space, for example:

  ``--cred first_auth second_auth``

  **IMPORTANT:** A credential must exist before you attempt to use it in a source and must be of the same type.

``--port=port``

  Optional. Sets a port to be used for the scan. This value supports connection and inspection on a non-standard port. By default, the a network scan runs on port 22 and a vcenter scan runs on port 443.

The information in a source might change as the structure of the network changes. Use the ``qpc source edit`` command to edit a source to accommodate those changes.

Although ``qpc source`` options can accept more than one value, the ``qpc source edit`` command is not additive. To edit a source and add a new value for an option, you must enter both the current and the new values for that option. Include only the options that you want to change in the ``qpc source edit`` command. Options that are not included are not changed.

**qpc source edit --name** *name*  **--type=** *(network | vcenter)* **[--hosts** *ip_address* **] [--cred** *credential* **] [--port=** *port* **]**

For example, if a source contains a value of ``server1creds`` for the ``--cred`` option, and you want to change that source to use both the ``server1creds`` and ``server2creds`` credentials, you would edit the source as follows:

``qpc source edit --name=mysource --cred server1creds server2creds``

**TIP:** After editing a source, use the ``qpc source show`` command to review those edits.

Listing and Showing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc source list`` command returns the details for all configured sources. The output of this command includes the host names, IP addresses, or IP ranges, the credentials, and the ports that are configured for each source.

**qpc source list **--type=** *(network | vcenter | satellite)* **

``--type=type``

  Optional.  Filter list results by source type.  Must be ``network``, ``vcenter``, or ``satellite``.


The ``qpc source show`` command is the same as the ``qpc source list`` command, except that it returns details for a single specified source.

**qpc source show --name=** *source*

``--name=source``

  Required. Contains the source to display.


Clearing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some sources. Use the ``qpc source clear`` command to delete sources.

**qpc source clear (--name=** *name* **| --all)**

``--name=name``

  Contains the source to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored sources. Mutually exclusive with the ``--name`` option.


Scanning
--------

Use the ``qpc scan start`` command to run connect and inspection scans on the sources. This command scans all of the host names or IP addresses that are defined in the supplied source, and then writes the report information to a comma separated values (CSV) file. Note: Any ssh-agent connection setup for a target host '
              'will be used as a fallback if it exists.

**qpc scan start --sources=** *source_list* **[--max-concurrency=** *concurrency* **]**

``--sources=source_list``

  Required. Contains the list of names of the sources to use to run the scan.

``--max-concurrency=concurrency``

  The number of parallel system scans. If not provided the default of 50 is utilized.

Listing and Showing Scans
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc scan list`` command returns the details for all executed scans. The output of this command includes the identifier, the source, and the status of the scan.

**qpc scan list** **--type=** *(connect | inspect)* **--type=** *(created | pending | running | paused | canceled | completed | failed)*

``--state=state``

  Optional. Filter list by scan state.  Must be ``created``, ``pending``, ``running``, ``paused``, ``canceled``, ``completed`` or ``failed``.

``--type=type``

  Optional. Filter list by scan type.  Must be ``connect`` or ``inspect``.

The ``qpc scan show`` command is the same as the ``qpc scan list`` command, except that it returns details for a single specified scan.

**qpc scan show --id=** *scan_identifier* **[--results]**

``--id=scan_identifier``

  Required. Contains the scan identifier to display.

``--results``

    Optional. Displays the results of the scan instead of the status.

Controlling Scans
~~~~~~~~~~~~~~~~~

When scans are queued and running you may have the need to control the execution of scans due to various factors.

The ``qpc scan pause`` command will hault the execution of a scan, but allow for it to be restarted at a later time.

**qpc scan pause --id=** *scan_identifier*

``--id=scan_identifier``

  Required. Contains the scan identifier to pause.


The ``qpc scan restart`` command will restart the execution of a scan that had previously been paused.

**qpc scan restart --id=** *scan_identifier*

``--id=scan_identifier``

  Required. Contains the scan identifier to restart.


The ``qpc scan cancel`` command will cancel the execution of a scan.

**qpc scan cancel --id=** *scan_identifier*

``--id=scan_identifier``

  Required. Contains the scan identifier to cancel.


Options for All Commands
------------------------

The following options are available for every Quipucords command.

``--help``

  Prints the help for the ``qpc`` command or subcommand.

``-v``

  Enables the verbose mode. The ``-vvv`` option increases verbosity to show more information. The ``-vvvv`` option enables connection debugging.

Examples
--------

:Creating a new network type credential with a keyfile: ``qpc cred add --name=new-creds **--type=** *network* --username=qpc-user --sshkeyfile=/etc/ssh/ssh_host_rsa_key``
:Creating a new network type credential with a password: ``qpc cred add --name=other-creds **--type=** *network* --username=qpc-user-pass --password``
:Creating a new vcenter type credential: ``qpc cred add --name=vcenter-cred **--type=** *vcenter* --username=vc-user-pass --password``
:Creating a new network source: ``qpc source add --name=new-source --type network --hosts 1.192.0.19 1.192.0.20 --cred new-creds``
:Creating a new vcenter source: ``qpc source add --name=new-source --type vcenter --hosts 1.192.0.19 --cred vcenter-cred``
:Editing a source: ``qpc source edit --name=new-source --hosts 1.192.0.[0:255] --cred new-creds other-creds``
:Running a scan with a source: ``qpc scan start --sources new-source``

Security Considerations
-----------------------

The credential credentials that are used to access servers are stored with the source in an AES-256 encrypted value within a database. A vault password is used to encrpyt/decrypt values. The vault password and decrypted values are in the system memory, and could theoretically be written to disk if memory swapping is enabled.

Authors
-------

Quipucords was originally written by Chris Hambridge <chambrid@redhat.com>, Noah Lavine <nlavine@redhat.com>, and Kevan Holdaway<kholdawa@redhat.com>.

Copyright
---------

(c) 2018 Red Hat, Inc. Licensed under the GNU Public License version 3.
