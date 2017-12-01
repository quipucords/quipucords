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

Quipucords uses two types of configuration to manage the discovery and inspection process. A *stored credential* contains credentials such as the username and password or SSH key of the user that runs the discovery and inspection process.  A *source* defines the network, such as a host, subnet, or network that is being monitored, plus includes one or more stored credentials to use to access that network during the discovery and inspection process. You can save multiple credentials and sources to use with Quipucords in various combinations as you run discovery and inspection processes, or *scans*.

By default, the stored credentials and sources that are created when using Quipucords are encrypted in a database. The values are encrypted with AES-256 encryption and are decrypted when the Quipucords server executes a scan, by using a *vault password* to access the encrypted values stored in the database.

Quipucords is an *agentless* discovery and inspection tool, so there is no need to install the tool on multiple systems. Discovery and inspection for the entire network is centralized on a single machine.

This man page describes the commands, subcommands, and options for the ``qpc`` command and includes basic usage information. For more detailed information and examples, including best practices, see the Quipucords README file.

Usage
-----

``qpc`` performs four major tasks:

* Creating stored credentials:

  ``qpc credential add ...``

* Creating sources:

  ``qpc source add --name=X --hosts X Y Z --credential A B``

* Running a scan:

  ``qpc scan start --source=X``

* Working with scans:

  ``qpc scan show --id=X``

The following sections describe these commands, their subcommands, and their options in more detail.

Stored Credentials
-----------------------

Use the ``qpc credential`` command to create and manage stored credentials.

A stored credential defines a set of user credentials to be used during a scan. These user credentials include a username and a password or SSH key. Quipucords uses SSH to connect to servers on the network and uses stored credentials to obtain the user credentials that are required to access those servers.

When a scan runs, it uses a source that contains the host names or IP addresses to be accessed. The source also contains references to the stored credentials that are required to access those systems. A single source can contain a reference to multiple stored credentials as needed to connect to all systems in that network.

Creating and Editing Stored Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a stored credential, supply SSH credentials as either a username-password pair or a username-key pair. Quipucords stores each set of credentials in a separate stored credential entry.

**qpc credential add --name=** *name* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **[--sudo-password]**

``--name=name``

  Required. Sets the name of the new stored credential. For the value, use a descriptive name that is meaningful to your organization. For example, you could identify the user or server that the stored credential relates to, such as ``admin12`` or ``server1_jdoe``. Do not include the password as part of this value, because the value for the ``--name`` option might be logged or printed during ``qpc`` execution.

``--username=username``

  Required. Sets the username of the SSH identity that is used to bind to the server.

``--password``

  Prompts for the password for the ``--username`` identity. Mutually exclusive with the ``--sshkeyfile`` option.

``--sshkeyfile=key_file``

  Sets the path of the file that contains the private SSH key for the ``--username`` identity. Mutually exclusive with the ``--password`` option.

``--sshpassphrase``

  Prompts for the passphrase to be used when connecting using an ssh keyfile that requires a passphrase. Can only be used with the ``--sshkeyfile`` option.

``--sudo-password``

  Prompts for the password to be used when running a command that uses sudo on the systems to be scanned.


The information in a stored credential, such as a password, sudo password, SSH keys, or even the username, might change. For example, network security might require passwords to be updated every few months. Use the ``qpc credential edit`` command to change the SSH credential information in a stored credential. The parameters for ``qpc credential edit`` are the same as those for ``qpc credential add``.

**qpc credential edit --name=** *name* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **[--sudo-password]**

Listing and Showing Stored Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc credential list`` command returns the details for every stored credential that is configured for Quipucords. This output includes the name, username, password, SSH keyfile and sudo password for each entry. Passwords are masked if provided, if not, they will appear as ``null``.

**qpc credential list**


The ``qpc credential show`` command is the same as the ``qpc credential list`` command, except that it returns details for a single specified stored credential.

**qpc credential show --name=** *name*

``--name=name``

  Required. Contains the stored credential entry to display.


Clearing Stored Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some stored credentials. Use the ``clear`` subcommand to delete stored credentials.

**IMPORTANT:** Remove or change the stored credential from any source that uses it *before* clearing a stored credential. Otherwise, any attempt to use the source to run a scan runs the command with a nonexistent stored credential, an action that causes the ``qpc`` command to fail.

**qpc credential clear (--name** *name* **| --all)**

``--name=name``

  Contains the stored credential to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored stored credentials. Mutually exclusive with the ``--name`` option.


Sources
----------------

Use the ``qpc source`` command to create and manage sources.

A source defines a collection of network information, including IP addresses or host names, SSH ports, and SSH credentials. The SSH credentials are provided through reference to one or more stored credentials. A discovery and inspection scan can reference a source so that the act of running the scan is automatic and repeatable, without a requirement to reenter network information for each scan attempt.

Creating and Editing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a source, supply one or more host names or IP addresses to connect to with the ``--hosts`` option and the stored credentials needed to access those systems with the ``--credential`` option. The ``qpc source`` command allows multiple entries for each of these options. Therefore, a single source can access a collection of servers and subnets as needed to create an accurate and complete scan.

**qpc source add --name=** *name* **--hosts** *ip_address* **--credential** *credential* **[--sshport=** *ssh_port* **]**

``--name=name``

  Required. Sets the name of the new source. For the value, use a descriptive name that is meaningful to your organization, such as ``APSubnet`` or ``Lab3``.

``--hosts ip_address``

  Sets the host name, IP address, or IP address range to use when running a scan. You can also provide a path for a file that contains a list of host names or IP addresses or ranges, where each item is on a separate line. The following examples show several different formats that are allowed as values for the ``--hosts`` option:

  * A specific host name:

    --hosts server.example.com

  * A specific IP address:

    --hosts 192.0.2.19

  * An IP address range:

    --hosts 192.0.2.[0:255]
    or
    --hosts 192.0.2.0/24

  * A file:

    --hosts /home/user1/hosts_file

``--credential credential``

  Contains the name of the stored credential to use to authenticate to the systems that are being scanned. If the individual systems that are being scanned each require different authentication credentials, you can use more than one stored credential. To add multiple stored credentials to the source, separate each value with a space, for example:

  ``--credential first_auth second_auth``

  **IMPORTANT:** A stored credential must exist before you attempt to use it in a source.

``--sshport=ssh_port``

  Sets a port to be used for the scan. This value supports discovery and inspection on a non-standard port. By default, the scan runs on port 22.

The information in a source might change as the structure of the network changes. Use the ``qpc source edit`` command to edit a source to accommodate those changes.

Although ``qpc source`` options can accept more than one value, the ``qpc source edit`` command is not additive. To edit a source and add a new value for an option, you must enter both the current and the new values for that option. Include only the options that you want to change in the ``qpc source edit`` command. Options that are not included are not changed.

**qpc source edit --name** *name* **[--hosts** *ip_address* **] [--credential** *credential* **] [--sshport=** *ssh_port* **]**

For example, if a source contains a value of ``server1creds`` for the ``--credential`` option, and you want to change that source to use both the ``server1creds`` and ``server2creds`` stored credentials, you would edit the source as follows:

``qpc source edit --name=mysource --credential server1creds server2creds``

**TIP:** After editing a source, use the ``qpc source show`` command to review those edits.

Listing and Showing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc source list`` command returns the details for all configured sources. The output of this command includes the host names, IP addresses, or IP ranges, the stored credentials, and the ports that are configured for each source.

**qpc source list**


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

Use the ``qpc scan`` command to run discovery and inspection scans on the network. This command scans all of the host names or IP addresses that are defined in the supplied source, and then writes the report information to a comma separated values (CSV) file. Note: Any ssh-agent connection setup for a target host '
              'will be used as a fallback if it exists.

**qpc scan --source=** *source_name* **[--max-concurrency=** *concurrency* **]**

``--source=source_name``

  Required. Contains the name of the source to use to run the scan.

``--max-concurrency=concurrency``

  The number of parallel system scans. If not provided the default of 50 is utilized.

Listing and Showing Scans
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc scan list`` command returns the details for all executed scans. The output of this command includes the identifier, the source, and the status of the scan.

**qpc scan list**


The ``qpc scan show`` command is the same as the ``qpc scan list`` command, except that it returns details for a single specified scan.

**qpc scan show --id=** *scan_identifier*

``--id=scan_identifier``

  Required. Contains the scan identifier to display.


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

:Creating a new stored credential with a keyfile: ``qpc credential add --name=new-creds --username=qpc-user --sshkeyfile=/etc/ssh/ssh_host_rsa_key``
:Creating a new stored credential with a password: ``qpc credential add --name=other-creds --username=qpc-user-pass --password``
:Creating a new source: ``qpc source add --name=new-source --hosts 1.192.0.19 --credential new-creds``
:Editing a source: ``qpc source edit --name=new-source --hosts 1.192.0.[0:255] --credential new-creds other-creds``
:Running a scan with a source: ``qpc scan --source=new-source``

Security Considerations
-----------------------

The stored credential credentials that are used to access servers are stored with the source in an AES-256 encrypted value within a database. A vault password is used to encrpyt/decrypt values. The vault password and decrypted values are in the system memory, and could theoretically be written to disk if memory swapping is enabled.

Authors
-------

Quipucords was originally written by Chris Hambridge <chambrid@redhat.com>, Noah Lavine <nlavine@redhat.com>, and Kevan Holdaway<kholdawa@redhat.com>.

Copyright
---------

(c) 2017 Red Hat, Inc. Licensed under the GNU Public License version 3.
