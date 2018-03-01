Getting Started with Quipucords
===============================
You use the capabilities of Quipucords to inspect and gather information on your IT infrastructure. The following information describes how you use the qpc command line interface to complete common Quipucords tasks. The complete list of options for each qpc command and subcommand are listed in the qpc man page.

Quipucords requires the configuration of two basic structures to manage the inspection process. A *credential* contains the access credentials, such as the username and password or SSH key of the user, with sufficient authority to run the inspection process on a particular source. For more information about this authority, see `Requirements <requirements.html>`_. A *source* defines the entity or entities to be inspected, such as a host, subnet, network, or systems management solution such as vCenter Server or Satellite. When you create a source, you also include one or more of the configured credentials to use to access the individual entities in the source during the inspection process.

You can save multiple credentials and sources to use with Quipucords in various combinations as you run inspection processes, or *scans*. When you have completed a scan, you can access the collection of *facts* in the output as a *report* to review the results.

Before You Begin: Check the Connection to the Quipucords Server
---------------------------------------------------------------
In some organizations, a single person might be responsible for scanning IT resources. However, in others, multiple people might hold this responsibility. Any additional Quipucords users who did not install the Quipucords server and command line tool must ensure that their command line tool instance is configured to connect to the server and that they can log in to the command line interface.

For more information, see the following sections:

- `Configuring the qpc Command Line Tool Connection <configure.html#connection>`_
- `Logging in to and Logging out of the qpc Command Line Interface <configure.html#login>`_.

Creating Credentials and Sources for the Different Source Types
---------------------------------------------------------------
The type of source that you are going to inspect determines the type of data that is required for credential and source configuration. Quipucords currently supports the following source types in the source creation command:

- network
- vcenter
- satellite

A *network* source is composed of one or more host names, one or more IP addresses, IP ranges, or a combination of these network resources. A *vcenter*, for vCenter Server, or *satellite*, for Satellite, source is created with the IP address or host name of that system management solution server.

In addition, the source creation command references one or more credentials. Typically, a network source might include multiple credentials because it is expected that many credentials would be needed to access a broad IP range. Conversely, a vcenter or satellite source would typically use a single credential to access a particular system management solution server.

The following scenarios provide examples of how you would create a network, vcenter, or satellite source and create the credentials required for each.

Creating a Network Source
^^^^^^^^^^^^^^^^^^^^^^^^^
To create a network source, use the following steps:

1. Create at least one network credential with root-level access:

   ``# qpc cred add --type network --name cred_name --username root_name [--sshkeyfile key_file] [--password]``

   If you did not use the ``sshkeyfile`` option to provide an SSH key for the username value, enter the password of the user with root-level access at the connection password prompt.

   If you want to use SSH keyfiles in the credential, you must copy the keys into the directory that you mapped to ``/sshkeys`` during Quipucords server configuration. In the example information for that procedure, that directory is ``~/quipucords/sshkeys``. The server references these files locally, so refer to the keys as if they are in the ``/sshkeys`` directory from the qpc command.

   For example, for a network credential where the ``/sshkeys`` directory for the server is mapped to ``~/quipucords/sshkeys``, the credential name is ``roothost1``, the user with root-level access is ``root``, and the SSH key for the user is in the ``~/.ssh/id_rsa`` file, you would enter the following commands:

   ``# cp ~/.ssh/id_rsa ~/quipucords/sshkeys``
   ``# qpc cred add --type network --name roothost1 --username root --sshkeyfile /sshkeys/id_rsa``

   Privilege escalation with the ``become-method``, ``become-user``, and ``become-password`` options is also supported to create a network credential for a user to obtain root-level access. You can use the ``become-*`` options with either the ``sshkeyfile`` or the ``password`` option.

   For example, for a network credential where the credential name is ``sudouser1``, the user with root-level access is ``sysadmin``, and the access is obtained through the password option, you would enter the following command:

   ``# qpc cred add --type network --name sudouser1 --username sysadmin --password --become-password``

   After you enter this command, you are prompted to enter two passwords. First, you would enter the connection password for the ``username`` user, and then you would enter the password for the ``become-method``, which is the ``sudo`` command by default.

2. Create at least one network source that specifies one or more network identifiers, such as a host name or host names, an IP address, a list of IP addresses, or an IP range, and one or more network credentials to be used for the scan.

   **TIP:** You can provide IP range values in CIDR or Ansible notation.

   ``# qpc source add --type network --name source_name --hosts host_name_or_file --cred cred_name``

   For example, for a network source where the source name is ``mynetwork``, the network to be scanned is the ``192.0.2.0/24`` subnet, and the network credentials that are used to run the scan are ``roothost1`` and ``roothost2``, you would enter the following command:

   ``# qpc source add --type network --name mynetwork --hosts 192.0.2.[1:254] --cred roothost1 roothost2``

   You can also use a file to pass in the network identifiers. If you use a file to enter multiple network identifiers, such as multiple individual IP addresses, enter each on a single line. For example, for a network profile where the path to this file is ``/home/user1/hosts_file``, you would enter the following command::

   ``# qpc source add --type network --name mynetwork --hosts /home/user1/hosts_file --cred roothost1 roothost2``


Creating a vCenter Source
^^^^^^^^^^^^^^^^^^^^^^^^^
To create a vcenter source, use the following steps:

1. Create at least one vcenter credential:

   ``# qpc cred add --type vcenter --name cred_name --username vcenter_user --password``

   Enter the password of the user with access to vCenter Server at the connection password prompt.

   For example, for a vcenter credential where the credential name is ``vcenter_admin`` and the user with access to the vCenter Server server is ``admin``, you would enter the following command::

   ``# qpc cred add --type vcenter --name vcenter_admin --username admin --password``

2. Create at least one vcenter source that specifies the host name or IP address of the server for vCenter Server and one vcenter credential to be used for the scan:

   ``# qpc source add --type vcenter --name source_name --hosts host_name --cred cred_name``

   For example, for a vcenter source where the source name is ``myvcenter``, the server for the vCenter Server is located at the ``192.0.2.10`` IP address, and the vcenter credential for that server is ``vcenter_admin``, you would enter the following command:

   ``# qpc source add --type vcenter --name myvcenter --hosts 192.0.2.10 --cred vcenter_admin``

   **IMPORTANT:** By default, sources are scanned with full SSL validation, but you might need to adjust the level of SSL validation to connect properly to the server for vCenter Server. The ``source add`` command supports options that are commonly used to downgrade the SSL validation. The ``--ssl-cert-verify`` option can take a value of ``False`` to disable SSL certificate validation; this option would be used for any server with a self-signed certificate. The ``--disable-ssl`` option can take a value of ``True`` to connect to the server over standard HTTP.

Creating a Satellite Source
^^^^^^^^^^^^^^^^^^^^^^^^^^^
To create a satellite source, use the following steps:

1. Create at least one satellite credential:

   ``# qpc cred add --type satellite --name cred_name --username satellite_user --password``

   Enter the password of the user with access to the Satellite server at the connection password prompt.

   For example, for a satellite credential where the credential name is ``satellite_admin`` and the user with access is to the Satellite server is ``admin``, you would enter the following command:

   ``# qpc cred add --type satellite --name satellite_admin --username admin --password``

2. Create at least one satellite source that specifies the host name or IP address of the Satellite server, one satellite credential to be used for the scan, and the version of the Satellite server (supported version values are ``6.2``, ``6.3``):

   ``# qpc source add --type satellite --name source_name --hosts host_name --cred cred_name --satellite-version sat_ver``

   For example, for a satellite source where the source name is ``mysatellite6``, the Satellite server is located at the ``192.0.2.15`` IP address, the satellite credential for that server is ``satellite_admin``, and the version of the Satellite server is ``6.2``, you would enter the following command:

   ``# qpc source add --type satellite --name mysatellite6 --hosts 192.0.2.15 --cred satellite_admin --satellite-version 6.2``

   **IMPORTANT:** By default, sources are scanned with full SSL validation, but you might need to adjust the level of SSL validation to connect properly to the Satellite server. The ``source add`` command supports options that are commonly used to downgrade the SSL validation. The ``--ssl-cert-verify`` option can take a value of ``False`` to disable SSL certificate validation; this option would be used for any server with a self-signed certificate. The Satellite server does not support disabling SSL, so the ``--disable-ssl`` option has no effect.

Creating a Scan
---------------
After you set up your credentials and sources, you can run a Quipucords scan to inspect your IT environment. You can create a scan on a single source or combine sources, even sources of different types.

To create a scan, use the following steps:

Create the scan by using the ``scan add`` command, specifying a name for the ``name`` option and one or more sources for the ``sources`` option:

  ``# qpc scan add --name scan1 --sources source_name1 source_name2``

For example, if you want to create a scan called ``myscan`` with the network source ``mynetwork`` and the Satellite source ``mysatellite6``, you would enter the following command:

  ``# qpc scan add --name myscan --sources mynetwork mysatellite6``

Running a Scan
--------------

**IMPORTANT:** Scans run consecutively on the Quipucords server, in the order in which the ``qpc scan start`` command for each scan is entered.

To run a scan, use the following steps:

Run the scan by using the ``scan start`` command, specifying the name of a scan for the ``name`` option:

  ``# qpc scan start --name scan_name1``

For example, if you want to run the scan ``myscan``, you would enter the following command:

  ``# qpc scan start --name myscan``

Showing Scan Job Results for an Active Scan
-------------------------------------------
When you run the ``scan start`` command, the output provides an identifier for that scan job. You can show the scan job results to follow the status of the scan job by using the ``scan job`` command and specifying the provided identifier.

**IMPORTANT:** The ``scan job`` command can show results only after the scan job starts running. You can also use this command on a scan job that is completed.

For example, you could run the following scan as the first scan in your environment:

  ``# qpc scan start --name myscan``

The output for the command shows the following information, with ``1`` listed as the scan job identifier.

  ``Scan "1" started``

To show the scan results to follow the status of that scan, you would enter the following command:

  ``# qpc scan job --id 1``

Listing Scan Results
--------------------
In addition to showing the status of a single scan job, you can also show a list of all scans that are in progress or are completed for a particular scan. To show this list of scan jobs, you use the ``scan job`` command. The output of this command includes the scan job identifier, the source or sources for that scan, and the current state of the scan.

  ``# qpc scan job --name scan_name1``

Viewing the Scan Report
-----------------------
When the scan job completes, you have the capability to produce a report for that scan. You can request a report with all the details, or facts, of the scan, or request a report with a summary. The summary report process runs steps to deduplicate and merge the facts found during the inspection of the various hosts that are contacted during the scan. For both types of reports, you can produce the report in JavaScript Object Notation (JSON) format or comma-separated values (CSV) format.

To generate a summary report, enter the ``report summary`` command and specify the identifier for the scan job and the format for the output file.

For example, if you want to create the report summary for a scan with the scan job identifier of ``1`` and you want to generate that report in CSV format in the ``~/scan_result.csv`` file, you would enter the following command:

  ``# qpc report summary --id 1 --csv --output-file=~/scan_result.csv``

However, if you want to create the detailed report, you would use the ``report detail`` command.  This command takes the same options as the ``report summary`` command. The output is not deduplicated and merged, so it contains all facts from each source. For example, to create the detailed report for a scan with the scan job identifer ``1``, with CSV output in the ``~/scan_result.csv`` file, you would enter the following command:

  ``# qpc report detail --id 1 --csv --output-file=~/scan_result.csv``

Pausing and Restarting a Scan
-----------------------------
As you use Quipucords, you might need to stop a currently running scan. There might be various business reasons that require you to do this, for example, the need to do an emergency fix due to an alert from your IT health monitoring system or the need to run a higher priority scan if a lower priority scan is currently running.

When you stop a scan by using the ``scan pause`` command, you can restart that same scan by using the ``scan restart`` command. To pause and restart a scan, use the following steps:

1. Make sure that you have the scan job identifier for the currently running scan. To obtain the scan job identifier, see the information in `Showing Scan Job Results for an Active Scan`_.

2. Enter the command to pause the scan. For example, if the scan job identifier is ``1``, you would enter the following command:

  ::

    # qpc scan pause --id 1

3. When you are ready to start the scan again, enter the command to restart the scan. For example, to restart scan ``1``, you would enter the following command:

  ::

    # qpc scan restart --id 1
