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

Quipucords, accessed through the ``qpc`` command, is an inspection and reporting tool. It is designed to identify environment data, or *facts*, such as the number of physical and virtual systems on a network, their operating systems, and other configuration data. In addition, it is designed to identify and report more detailed facts for some versions of key Red Hat packages and products for the Linux based IT resources in that network. The ability to inspect the software and systems that are running on your network improves your ability to understand and report on your entitlement usage. Ultimately, this inspection and reporting process is part of the larger system administration task of managing your inventories.

Quipucords uses two types of configuration to manage the inspection process. A *credential* contains configuration such as the user name and password or SSH key of the user that runs the inspection process.  A *source* defines the entity to be inspected, such as a host, subnet, network, or systems management solution such as vCenter Server or Satellite, plus includes one or more credentials to use to access that network or systems management solution during the inspection process. You can save multiple credentials and sources to use with Quipucords in various combinations as you run inspection processes, or *scans*. When you have completed a scan, you can access the output as a *report* to review the results.

By default, the credentials and sources that are created when using Quipucords are encrypted in a database. The values are encrypted with AES-256 encryption. They are decrypted when the Quipucords server runs a scan, by using a *vault password* to access the encrypted values that are stored in the database.

Quipucords is an *agentless* inspection tool, so there is no need to install the tool on the sources to be inspected.

This manual page describes the commands, subcommands, and options for the ``qpc`` command and includes usage information and example commands.

Usage
-----

The ``qpc`` command has several subcommands that encompass the inspection and reporting workflow. Within that workflow, ``qpc`` performs the following major tasks:

* Logging in to the server:

  ``qpc server login --username admin``

* Creating credentials:

  ``qpc cred add --name=credname1 --type=type --username=user1 --password``

* Creating sources:

  ``qpc source add --name=sourcename1 --type=type --hosts server1.example.com server2.example.com --cred credname1 credname2``

* Creating scans:

  ``qpc scan add --name=scan1 --sources sourcename1 sourcename2``

* Running a scan:

  ``qpc scan start --name=scan1``

* Working with scans:

  ``qpc scan show --name=scan1``

* Working with scan jobs:

  ``qpc scan job --id=1``

* Generating reports:

  ``qpc report summary --id 1 --csv --output-file=~/scan_result.csv``

The following sections describe these commands, their subcommands, and their options in more detail. They also describe additional tasks that are not highlighted in the previous list of major workflow tasks.

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

  Optional. Sets the port to use to connect to the server. The default is ``443``.


Logging in to the server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To log in to the server after the connection is configured, use the ``login`` subcommand. This command retrieves a token that is used for authentication with subsequent command line interface commands.

**qpc server login [--username=** *username* **]**

``--username=username``

  Optional. Sets the user name that is used to log in to the server.


Logging out of the server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To log out of the server, use the ``logout`` subcommand. This command removes the token that was created when the ``login`` command was used.

**qpc server logout**


Credentials
-----------

Use the ``qpc cred`` command to create and manage credentials.

A credential contains a set of user authentication information to be used during a scan. A credential includes a user name and a password or SSH key. Quipucords uses SSH to connect to servers on the network and uses credentials to access those servers.

When a scan runs, it uses a source that contains information such as the host names, IP addresses, a network, or a systems management solution to be accessed. The source also contains references to the credentials that are required to access those systems. A single source can contain a reference to multiple credentials as needed to connect to all systems in that network or systems management solution.

Creating and Editing Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a credential, supply the type of credential and supply SSH credentials as either a user name-password pair or a user name-key pair. Quipucords stores each set of credentials in a separate credential entry.

**qpc cred add --name=** *name* **--type=** *(network | vcenter | satellite)* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **--become-method=** *(sudo | su | pbrun | pfexec | doas | dzdo | ksu | runas )* **--become-user=** *user* **[--become-password]**

``--name=name``

  Required. Sets the name of the new credential. For the value, use a descriptive name that is meaningful to your organization. For example, you could identify the user or server that the credential relates to, such as ``admin12`` or ``server1_jdoe``. Do not include the password as part of this value, because the value for the ``--name`` option might be logged or printed during ``qpc`` execution.

``--type=type``

  Required. Sets the type of credential. The value must be ``network``, ``vcenter``, or ``satellite``. The type cannot be edited after a credential is created.

``--username=username``

  Required. Sets the user name of the SSH identity that is used to bind to the server.

``--password``

  Prompts for the password for the ``--username`` identity. Mutually exclusive with the ``--sshkeyfile`` option.

``--sshkeyfile=key_file``

  Sets the path of the file that contains the private SSH key for the ``--username`` identity. Mutually exclusive with the ``--password`` option.

``--sshpassphrase``

  Prompts for the passphrase to be used when connecting with an SSH keyfile that requires a passphrase. Can only be used with the ``--sshkeyfile`` option.

``--become-method=become_method``

  Sets the method to become for privilege escalation when running a network scan. The value must be ``sudo``, ``su``, ``pbrun``, ``pfexec``, ``doas``, ``dzdo``, ``ksu``, or ``runas``. The default is set to ``sudo`` when the credential type is ``network``.

``--become-user=user``

  Sets the user to become when running a privileged command during a network scan.

``--become-password``

  Prompts for the privilege escalation password to be used when running a network scan.

The information in a credential, such as a password, become password, SSH keys, the become_method, or even the user name, might change. For example, network security might require passwords to be updated every few months. Use the ``qpc cred edit`` command to change credential information. The parameters for ``qpc cred edit`` are the same as those for ``qpc cred add``.

**qpc cred edit --name=** *name* **--username=** *username* **(--password | --sshkeyfile=** *key_file* **)** **[--sshpassphrase]** **--become-method=** *(sudo | su | pbrun | pfexec | doas | dzdo | ksu | runas )* **--become-user=** *user* **[--become-password]**

Listing and Showing Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc cred list`` command returns the details for every credential that is configured for Quipucords. This output includes the name, user name, password, SSH keyfile, and sudo password for each entry. Passwords are masked if provided, if not, they will appear as ``null``.

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

A source contains a single entity or a set of multiple entities that are to be inspected. A source can be a single physical machine, virtual machine, or container, or it can be a collection of network information, including IP addresses or host names, or information about a systems management solution such as vCenter Server or Satellite. The source also contains information about the SSH ports and SSH credentials that are needed to access the systems to be inspected. The SSH credentials are provided through reference to one or more of the Quipucords credentials that you configure.

When you configure a scan, it contains references to one or more sources, including the credentials that are provided in each source. Therefore, you can reference sources in different scan configurations for various purposes, for example, to scan your entire infrastructure or a specific sector of that infrastructure.

Creating and Editing Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a source, supply the type of source with the ``type`` option, one or more host names or IP addresses to connect to with the ``--hosts`` option, and the credentials needed to access those systems with the ``--cred`` option. The ``qpc source`` command allows multiple entries for the ``hosts`` and ``cred`` options. Therefore, a single source can access a collection of servers and subnets as needed to create an accurate and complete scan.

**qpc source add --name=** *name*  **--type=** *(network | vcenter | satellite)* **--hosts** *ip_address* **--cred** *credential* **[--exclude-hosts** *ip_address* **]** **[--port=** *port* **]** **[--use-paramiko=** *(True | False)* **]** **[--ssl-cert-verify=** *(True | False)* **]** **[--ssl-protocol=** *protocol* **]** **[--disable-ssl=** *(True | False)* **]**

``--name=name``

  Required. Sets the name of the new source. For the value, use a descriptive name that is meaningful to your organization, such as ``APSubnet`` or ``Lab3``.

``--type=type``

  Required. Sets the type of source.  The value must be ``network``, ``vcenter``, or ``satellite``. The type cannot be edited after a source is created.

``--hosts ip_address``

  Sets the host name, IP address, or IP address range to use when running a scan. You can also provide a path for a file that contains a list of host names or IP addresses or ranges, where each item is on a separate line. The following examples show several different formats that are allowed as values for the ``--hosts`` option:

  * A specific host name:

    ``--hosts server.example.com``

  * A specific IP address:

    ``--hosts 192.0.2.19``

  * An IP address range, provided in CIDR or Ansible notation. This value is only valid for the ``network`` type:

    ``--hosts 192.0.2.[0:255]``
    or
    ``--hosts 192.0.2.0/24``

  * A file:

    ``--hosts /home/user1/hosts_file``

``--exclude-hosts ip_address``

  Optional. Sets the host name, IP address, or IP address range to exclude when running a scan. Follows the same formatting options as ``--hosts`` shown above.

``--cred credential``

  Contains the name of the credential to use to authenticate to the systems that are being scanned. If the individual systems that are being scanned each require different authentication credentials, you can use more than one credential. To add multiple credentials to the source, separate each value with a space, for example:

  ``--cred first_auth second_auth``

  **IMPORTANT:** A credential must exist before you attempt to use it in a source. A credential must be of the same type as the source.

``--port=port``

  Optional. Sets a port to be used for the scan. This value supports connection and inspection on a non-standard port. By default, a network scan runs on port 22 and a vcenter or satellite scan runs on port 443.

``--use-paramiko=(True | False)``

  Optional. Changes the Ansible connection method from the default open-ssh to the python ssh implementation.

``--ssl-cert-verify=(True | False)``

  Optional. Determines whether SSL certificate validation will be performed for the scan.

``--ssl-protocol=protocol``

  Optional. Determines the SSL protocol to be used for a secure connection during the scan. The value must be ``SSLv23``, ``TLSv1``, ``LSv1_1``, or ``TLSv1_2``.

``--disable-ssl=(True | False)``

  Optional. Determines whether SSL communication will be disabled for the scan.

The information in a source might change as the structure of the network changes. Use the ``qpc source edit`` command to edit a source to accommodate those changes.

Although ``qpc source`` options can accept more than one value, the ``qpc source edit`` command is not additive. To edit a source and add a new value for an option, you must enter both the current and the new values for that option. Include only the options that you want to change in the ``qpc source edit`` command. Options that are not included are not changed.

**qpc source edit --name** *name* **[--hosts** *ip_address* **] [--cred** *credential* **] **[--exclude-hosts** *ip_address* **] [--port=** *port* **]** **[--use-paramiko=** *(True | False)* **]** **[--ssl-cert-verify=** *(True | False)* **]** **[--ssl-protocol=** *protocol* **]** **[--disable-ssl=** *(True | False)* **]**

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


Scans
-----

Use the ``qpc scan`` command to create, run and manage scans.

A scan contains a set of one or more sources of any type plus additional options that refine how the scan runs, such as the products to omit from the scan and the maximum number of parallel system scans. Because a scan can combine sources of different types, you can include network and systems management solution (such as Satellite and vCenter Server) sources in a single scan. When you configure a scan to include multiple sources of different types, for example, a network source and a satellite source, the same part of your infrastructure might be scanned more than once. The results for this type of scan could show duplicate information in the reported results. However, you have the option to view the unprocessed detailed report that would show these duplicate results, or a processed summary report with deduplicated and merged results.

The creation of a scan references the sources, the credentials contained within those sources, and the other options so that the act of running the scan is repeatable. When you run the scan, each instance is saved as a scan job.

Creating and Editing Scans
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use the ``qpc scan add`` command to create scan objects with one or more sources. This command creates a scan object that references the supplied sources and contains any options supplied by the user.

**qpc scan add --name** *name* **--sources=** *source_list* **[--max-concurrency=** *concurrency* **]** **[--disabled-optional-products=** *products_list* **]** **[--enabled-ext-product-search=** *products_list* **]** **[--ext-product-search-dirs=** *search_dirs_list* **]**

``--sources=source_list``

  Required. Contains the list of source names to use to run the scan.

``--max-concurrency=concurrency``

  Optional. Contains the maximum number of parallel system scans. If this value is not provided, the default is ``50``.

``--disabled-optional-products=products_list``

  Optional. Contains the list of products to exclude from inspection. Valid values are ``jboss_eap``, ``jboss_fuse``, ``jboss_ws``, and ``jboss_brms``.

``--enabled-ext-product-search=products_list``

  Optional. Contains the list of products to include for the extended product search. Extended product search is used to find products that might be installed in nondefault locations. Valid values are ``jboss_eap``, ``jboss_fuse``, ``jboss_ws``, and ``jboss_brms``.

``--ext-product-search-dirs=search_dirs_list``

  Optional. Contains a list of absolute paths of directories to search with the extended product search. This option uses the provided list of directories to search for the presence of Red Hat JBoss Enterprise Application Platform (EAP), Red Hat JBoss Fuse, and Red Hat Decision Manager (formerly Red Hat JBoss BRMS).

The information in a scan might change as the structure of the network changes. Use the ``qpc scan edit`` command to edit an existing scan to accommodate those changes.

Although ``qpc scan`` options can accept more than one value, the ``qpc scan edit`` command is not additive. To edit a scan and add a new value for an option, you must enter both the current and the new values for that option. Include only the options that you want to change in the ``qpc scan edit`` command. Options that are not included are not changed.

**qpc scan edit --name** *name* **[--sources=** *source_list* **]** **[--max-concurrency=** *concurrency* **]** **[--disabled-optional-products=** *products_list* **]** **[--enabled-ext-product-search=** *products_list* **]** **[--ext-product-search-dirs=** *search_dirs_list* **]**

For example, if a scan contains a value of ``network1source`` for the ``--sources`` option, and you want to change that scan to use both the ``network1source`` and ``satellite1source`` sources, you would edit the scan as follows:

``qpc scan edit --name=myscan --sources network1source satellite1source``

If you want to reset the ``--disabled-optional-products``, ``--enabled-ext-product-search``, or ``--ext-product-search-dirs`` back to their default values, you must provide the flag without any product values.

For example, if you want to reset the ``--disabled-optional-products`` option back to the default values, you would edit the scan as follows:

``qpc scan edit --name=myscan --disabled-optional-products``

**TIP:** After editing a scan, use the ``qpc scan show`` command to review those edits.

Listing and Showing Scans
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``qpc scan list`` command returns the summary details for all created scan objects or all created scan objects of a certain type. The output of this command includes the identifier, the source or sources, and any options supplied by the user.

**qpc scan list** **--type=** *(connect | inspect)*

``--type=type``

  Optional. Filters the results by scan type. This value must be ``connect`` or ``inspect``. A scan of type ``connect`` is a scan that began the process of connecting to the defined systems in the sources, but did not transition into inspecting the contents of those systems. A scan of type ``inspect`` is a scan that moves into the inspection process.

The ``qpc scan show`` command is the same as the ``qpc scan list`` command, except that it returns summary details for a single specified scan object.

**qpc scan show --name** *name*

``--name=name``

  Required. Contains the name of the scan object to display.

Clearing Scans
~~~~~~~~~~~~~~

As the network infrastructure changes, it might be necessary to delete some scan objects. Use the ``qpc scan clear`` command to delete scans.

**qpc scan clear (--name=** *name* **| --all)**

``--name=name``

  Contains the name of the source to clear. Mutually exclusive with the ``--all`` option.

``--all``

  Clears all stored scan objects. Mutually exclusive with the ``--name`` option

Scanning
--------

Use the ``qpc scan start`` command to create and run a scan job from an existing scan object. This command scans all of the host names or IP addresses that are defined in the supplied sources of the scan object from which the job is created. Each instance of a scan job is assigned a unique *identifier* to identify the scan results, so that the results data can be viewed later.

**IMPORTANT:** If any ssh-agent connection is set up for a target host, that connection will be used as a fallback connection.

**qpc scan start --name** *scan_name*

``--name=name``

  Contains the name of the scan object to run.

Viewing Scan Jobs
~~~~~~~~~~~~~~~~~

The ``qpc scan job`` command returns the list of scan jobs for a scan object or information about a single scan job for a scan object. For the list of scan jobs, the output of this command includes the scan job identifiers for each currently running or completed scan job, the current state of each scan job, and the source or sources for that scan. For information about a single scan job, the output of this command includes status of the scan job, the start time of the scan job, and (if applicable) the end time of the scan job.

**qpc scan job (--name** *scan_name* | **--id=** *scan_job_identifier* **) --status=** *(created | pending | running | paused | canceled | completed | failed)*

``--name=name``

  Contains the name of the scan object of which to display the scan jobs. Mutually exclusive with the ``--id`` option.

``--id=scan_job_identifier``

  Contains the identifier of a specified scan job to display. Mutually exclusive with the ``--name`` option.

``--status=status``

  Optional. Filters the results by scan job state. This value must be ``created``, ``pending``, ``running``, ``paused``, ``canceled``, ``completed``, or ``failed``.

Controlling Scans
~~~~~~~~~~~~~~~~~

When scan jobs are queued and running, you might need to control the execution of scan jobs due to the needs of other business processes in your organization. The ``pause``, ``restart``, and ``cancel`` subcommands enable you to control scan job execution.

The ``qpc scan pause`` command halts the execution of a scan job, but enables it to be restarted at a later time.

**qpc scan pause --id=** *scan_job_identifier*

``--id=scan_job_identifier``

  Required. Contains the identifier of the scan job to pause.


The ``qpc scan restart`` command restarts the execution of a scan job that is paused.

**qpc scan restart --id=** *scan_job_identifier*

``--id=scan_job_identifier``

  Required. Contains the identifier of the scan job to restart.


The ``qpc scan cancel`` command cancels the execution of a scan job. A canceled scan job cannot be restarted.

**qpc scan cancel --id=** *scan_job_identifier*

``--id=scan_job_identifier``

  Required. Contains the identifier of the scan job to cancel.


Reports
--------

Use the ``qpc report`` command to generate a report from a scan. You can generate a report as JavaScript Object Notation (JSON) format or as comma-separated values (CSV) format. There are two different types of report that you can generate, a *detail* report and a *summary* report.


Viewing the Detail Report
~~~~~~~~~~~~~~~~~~~~~~~~~
The ``qpc report detail`` command generates a detailed report that contains the unprocessed facts that are gathered during a scan. These facts are the raw output from network, vcenter, and satellite scans, as applicable.

**qpc report detail (--scan-job** *scan_job_identifier* **|** **--report** *report_identifier* **)** **(--json|--csv)** **--output-file** *path*

``--scan-job=scan_job_identifier``

  Contains the scan job identifier for the scan that is used to generate the report. Mutually exclusive with the ``--report`` option.

``--report=report_identifier``

  Contains the report identifier to retrieve.  Mutually exclusive with the ``--scan-job`` option.

``--json``

  Displays the results of the report in JSON format. Mutually exclusive with the ``--csv`` option.

``--csv``

  Displays the results of the report in CSV format. Mutually exclusive with the ``--json`` option.

``--output-file=path``

  Required. Path to a file location where the report data is saved.

Viewing the Summary Report
~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``qpc report summary`` command generates a report that contains the processed fingerprints from a scan. A *fingerprint* is the set of system, product, and entitlement facts for a particular physical or virtual machine. A processed fingerprint results from a procedure that merges facts from various sources, and, when possible, deduplicates redundant systems.

For example, the raw facts of a scan that includes both network and vcenter sources could show two instances of a machine, indicated by an identical MAC address. The generation of a report summary results in a deduplicated and merged fingerprint that shows both the network and vcenter facts for that machine.

**qpc report summary (--scan-job** *scan_job_identifier* **|** **--report** *report_identifier* **)** **(--json|--csv)** **--output-file** *path*

``--scan-job=scan_job_identifier``

  Contains the scan job identifier for the scan that is used to generate the report. Mutually exclusive with the ``--report`` option.

``--report=report_identifier``

  Contains the report identifier to retrieve.  Mutually exclusive with the ``--scan-job`` option.

``--json``

  Displays the results of the report in JSON format. Mutually exclusive with the ``--csv`` option.

``--csv``

  Displays the results of the report in CSV format. Mutually exclusive with the ``--json`` option.

``--output-file=path``

  Required. Path to a file location where the report data is saved.

Merging Scan Job Results
~~~~~~~~~~~~~~~~~~~~~~~~
The ``qpc report merge`` command combines results from two or more scan job identifiers, report identifers, or JSON details report files to create a single report. The ``qpc report summary`` or ``qpc report detail`` can be used to obtain the report.

**qpc report merge (--job-ids** *scan_job_identifiers* **|** **--report-ids** *report_identifiers* **|** **--json-files** *json_details_report_files* **)**

``--job-ids=scan_job_identifiers``

  Contains the scan job identifiers that will be merged.  Mutually exclusive with the ``--report-ids`` option and the ``--json-files`` option.

``--report-ids=report_identifiers``

  Contains the report identifiers that will be merged.  Mutually exclusive with the ``--job-ids`` option and the ``--json-files`` option.

``--json-files=json_details_report_files``

  Contains the JSON details report files that will be merged.  Mutually exclusive with the ``--job-ids`` option and the ``--report-ids`` option.

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
Creating a new network source with an excluded host
  ``qpc source add --name=new_source --type network --hosts 1.192.1.[0:255] --exclude-hosts 1.192.1.19 --cred new_creds``
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

Quipucords was originally written by Chris Hambridge <chambrid@redhat.com>, Noah Lavine <nlavine@redhat.com>, Kevan Holdaway <kholdawa@redhat.com>, and Ashley Aiken <aaiken@redhat.com>.

Copyright
---------

Copyright 2018 Red Hat, Inc. Licensed under the GNU Public License version 3.
