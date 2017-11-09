qpc
===

Name
----

qpc - Discover and manage product entitlement metadata on your network.


Synopsis
--------

``qpc command subcommand [options]``

Description
-----------

Quipucords, and the ``qpc`` command, is a network discovery and inspection tool to identify environment data, or *facts*, such as the number of physical and virtual systems on a network, their operating systems and other configuration data, and versions of some key packages and products for almost any Linux or UNIX version. The ability to discover and inspect the software and systems that are running on the network improves your ability to understand and report on your entitlement usage. Ultimately, this discovery and inspection process is part of the larger system administration task of managing your inventories.

Quipucords uses two types of profiles to manage the discovery and inspection process. An *authentication profile* contains credentials such as the username and password or SSH key of the user that runs the discovery and inspection process.  A *network profile* defines the network, such as a host, subnet, or network that is being monitored, plus includes one or more authentication profiles to use to access that network during the discovery and inspection process. You can save multiple authentication profiles and network profiles to use with Quipucords in various combinations as you run discovery and inspection processes, or *scans*.

By default, the authentication profiles and network profiles that are created when using Quipucords are encrypted in a database. The values are encrypted with AES-256 encryption and are decrypted when the Quipucords server executes a scan, by using a *vault password* to access the encrypted values stored in the database.

Quipucords is an *agentless* discovery and inspection tool, so there is no need to install the tool on multiple systems. Discovery and inspection for the entire network is centralized on a single machine.

This man page describes the commands, subcommands, and options for the ``qpc`` command and includes basic usage information. For more detailed information and examples, including best practices, see the Quipucords README file.

Usage
-----

``qpc`` performs four major tasks:

* Creating authentication profiles:

  ``qpc auth add ...``

* Creating network profiles:

  ``qpc profile add --name=X --hosts X Y Z --auth A B``

* Running a scan:

  ``qpc scan start --profile=X``

* Working with scans:

  ``qpc scan show --id=X``

The following sections describe these commands, their subcommands, and their options in more detail.

Authentication Profiles
-----------------------

Use the ``qpc auth`` command to create and manage authentication profiles.

An authentication profile defines a set of user credentials to be used during a scan. These user credentials include a username and a password or SSH key. Quipucords uses SSH to connect to servers on the network and uses authentication profiles to obtain the user credentials that are required to access those servers.

When a scan runs, it uses a network profile that contains the host names or IP addresses to be accessed. The network profile also contains references to the authentication profiles that are required to access those systems. A single network profile can contain a reference to multiple authentication profiles as needed to connect to all systems in that network.

Creating and Editing Authentication Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create an authentication profile, supply SSH credentials as either a username-password pair or a username-key pair. Quipucords stores each set of credentials in a separate authentication profile entry.

**qpc auth add --name=** *name* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **[--sudo-password]**

``--name=name``

  Required. Sets the name of the new authentication profile. For the value, use a descriptive name that is meaningful to your organization. For example, you could identify the user or server that the authentication profile relates to, such as ``admin12`` or ``server1_jdoe``. Do not include the password as part of this value, because the value for the ``--name`` option might be logged or printed during ``qpc`` execution.

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


The information in an authentication profile, such as a password, sudo password, SSH keys, or even the username, might change. For example, network security might require passwords to be updated every few months. Use the ``qpc auth edit`` command to change the SSH credential information in an authentication profile. The parameters for ``qpc auth edit`` are the same as those for ``qpc auth add``.

**qpc auth edit --name=** *name* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **[--sudo-password]**

Listing and Showing Authentication Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc auth list`` command returns the details for every authentication profile that is configured for Quipucords. This output includes the name, username, password, SSH keyfile and sudo password for each entry. Passwords are masked if provided, if not, they will appear as ``null``.

**qpc auth list**


The ``qpc auth show`` command is the same as the ``qpc auth list`` command, except that it returns details for a single specified authentication profile.

**qpc auth show --name=** *name*

``--name=name``

  Required. Contains the authentication profile entry to display.


Clearing Authentication Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some authentication profiles. Use the ``clear`` subcommand to delete authentication profiles.

**IMPORTANT:** Remove or change the authentication profile from any network profile that uses it *before* clearing an authentication profile. Otherwise, any attempt to use the network profile to run a scan runs the command with a nonexistent authentication profile, an action that causes the ``qpc`` command to fail.

**qpc auth clear (--name** *name* **| --all)

``--name=name``

  Contains the authentication profile to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored authentication profiles. Mutually exclusive with the ``--name`` option.


Network Profiles
----------------

Use the ``qpc profile`` command to create and manage network profiles.

A network profile defines a collection of network information, including IP addresses or host names, SSH ports, and SSH credentials. The SSH credentials are provided through reference to one or more authentication profiles. A discovery and inspection scan can reference a network profile so that the act of running the scan is automatic and repeatable, without a requirement to reenter network information for each scan attempt.

Creating and Editing Network Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a network profile, supply one or more host names or IP addresses to connect to with the ``--hosts`` option and the authentication profiles needed to access those systems with the ``--auth`` option. The ``qpc profile`` command allows multiple entries for each of these options. Therefore, a single network profile can access a collection of servers and subnets as needed to create an accurate and complete scan.

**qpc profile add --name=** *name* **--hosts** *ip_address* **--auth** *auth_profile* **[--sshport=** *ssh_port* **]**

``--name=name``

  Required. Sets the name of the new network profile. For the value, use a descriptive name that is meaningful to your organization, such as ``APSubnet`` or ``Lab3``.

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

``--auth auth_profile``

  Contains the name of the authentication profile to use to authenticate to the systems that are being scanned. If the individual systems that are being scanned each require different authentication credentials, you can use more than one authentication profile. To add multiple authentication profiles to the network profile, separate each value with a space, for example:

  ``--auth first_auth second_auth``

  **IMPORTANT:** An authentication profile must exist before you attempt to use it in a network profile.

``--sshport=ssh_port``

  Sets a port to be used for the scan. This value supports discovery and inspection on a non-standard port. By default, the scan runs on port 22.

The information in a network profile might change as the structure of the network changes. Use the ``qpc profile edit`` command to edit a network profile to accommodate those changes.

Although ``qpc profile`` options can accept more than one value, the ``qpc profile edit`` command is not additive. To edit a network profile and add a new value for an option, you must enter both the current and the new values for that option. Include only the options that you want to change in the ``qpc profile edit`` command. Options that are not included are not changed.

**qpc profile edit --name** *name* **[--hosts** *ip_address* **] [--auth** *auth_profile* **] [--sshport=** *ssh_port* **]

For example, if a network profile contains a value of ``server1creds`` for the ``--auth`` option, and you want to change that network profile to use both the ``server1creds`` and ``server2creds`` authentication profiles, you would edit the network profile as follows:

``qpc profile edit --name=myprofile --auth server1creds server2creds``

**TIP:** After editing a network profile, use the ``qpc profile show`` command to review those edits.

Listing and Showing Network Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc profile list`` command returns the details for all configured network profiles. The output of this command includes the host names, IP addresses, or IP ranges, the authentication profiles, and the ports that are configured for each network profile.

**qpc profile list**


The ``qpc profile show`` command is the same as the ``qpc profile list`` command, except that it returns details for a single specified network profile.

**qpc profile show --name=** *profile*

``--name=profile``

  Required. Contains the network profile to display.


Clearing Network Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some network profiles. Use the ``qpc profile clear`` command to delete network profiles.

**qpc profile clear (--name=** *name* **| --all)**

``--name=name``

  Contains the network profile to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored network profiles. Mutually exclusive with the ``--name`` option.


Scanning
--------

Use the ``qpc scan`` command to run discovery and inspection scans on the network. This command scans all of the host names or IP addresses that are defined in the supplied network profile, and then writes the report information to a comma separated values (CSV) file. Note: Any ssh-agent connection setup for a target host '
              'will be used as a fallback if it exists.

**qpc scan --profile=** *profile_name* **[--max-concurrency=** *concurrency* **]**

``--profile=profile_name``

  Required. Contains the name of the network profile to use to run the scan.

``--max-concurrency=concurrency``

  The number of parallel system scans. If not provided the default of 50 is utilized.

Listing and Showing Scans
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc scan list`` command returns the details for all executed scans. The output of this command includes the identifier, the network profile, and the status of the scan.

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

:Creating a new authentication profile with a keyfile: ``qpc auth add --name=new-creds --username=qpc-user --sshkeyfile=/etc/ssh/ssh_host_rsa_key``
:Creating a new authentication profile with a password: ``qpc auth add --name=other-creds --username=qpc-user-pass --password``
:Creating a new profile: ``qpc profile add --name=new-profile --hosts 1.192.0.19 --auth new-creds``
:Editing a profile: ``qpc profile edit --name=new-profile --hosts 1.192.0.[0:255] --auth new-creds other-creds``
:Running a scan with a profile: ``qpc scan --profile=new-profile``

Security Considerations
-----------------------

The authentication profile credentials that are used to access servers are stored with the network profile in an AES-256 encrypted value within a database. A vault password is used to encrpyt/decrypt values. The vault password and decrypted values are in the system memory, and could theoretically be written to disk if memory swapping is enabled.

Authors
-------

Quipucores was originally written by Chris Hambridge <chambrid@redhat.com>, Noah Lavine <nlavine@redhat.com>, and Kevan Holdaway<kholdawa@redhat.com>.

Copyright
---------

(c) 2017 Red Hat, Inc. Licensed under the GNU Public License version 3.
