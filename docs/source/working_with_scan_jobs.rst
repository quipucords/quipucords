Working with Scan Jobs
======================
Once a scan has been started you can view information about the created scan job to determine its state or to pause/cancel the operation.

Showing Scan Job Results for an Active Scan
-------------------------------------------
When you run the ``scan start`` command, the output provides an identifier for that scan job. You can show the scan job results to follow the status of the scan job by using the ``scan job`` command and specifying the provided identifier.

**IMPORTANT:** The ``scan job`` command can show results only after the scan job starts running. You can also use this command on a scan job that is completed.

For example, you could run the following scan as the first scan in your environment::

  # qpc scan start --name myscan

The output for the command shows the following information, with ``1`` listed as the scan job identifier::

  Scan "1" started

To show the scan results to follow the status of that scan, you would enter the following command::

  # qpc scan job --id 1

Listing Scan Results
--------------------
In addition to showing the status of a single scan job, you can also show a list of all scans jobs that are in progress or are completed for a particular scan. To show this list of scan jobs, you use the ``scan job`` command. The output of this command includes the scan job identifier, the source or sources for that scan, and the current state of the scan.

To show the list of scan results, enter the following command::

  # qpc scan job --name scan_name1

Pausing and Restarting a Scan
-----------------------------
As you use Quipucords, you might need to stop a currently running scan. There might be various business reasons that require you to do this, for example, the need to do an emergency fix due to an alert from your IT health monitoring system or the need to run a higher priority scan if a lower priority scan is currently running.

When you stop a scan by using the ``scan pause`` command, you can restart that same scan by using the ``scan restart`` command. To pause and restart a scan, use the following steps:

1. Make sure that you have the scan job identifier for the currently running scan. To obtain the scan job identifier, see the information in `Showing Scan Job Results for an Active Scan`_.

2. Enter the command to pause the scan job. For example, if the scan job identifier is ``1``, you would enter the following command::

    # qpc scan pause --id 1

3. When you are ready to start the scan job again, enter the command to restart the scan. For example, to restart scan ``1``, you would enter the following command::

    # qpc scan restart --id 1
