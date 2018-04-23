Working with Scans
------------------
A scan is an object that groups one or more sources into a unit that can be scanned in a reproducible way. The following information describes how to create scans and how to start scans.

Creating a Scan
^^^^^^^^^^^^^^^
After you set up your credentials and sources, you can run a Quipucords scan to inspect your IT environment. You can create a scan that uses a single source or combines sources, even sources of different types.

To create a scan, use the following steps:

Create the scan by using the ``scan add`` command, specifying a name for the ``name`` option and one or more sources for the ``sources`` option::

  # qpc scan add --name scan1 --sources source_name1 source_name2

For example, if you want to create a scan called ``myscan`` with the network source ``mynetwork`` and the Satellite source ``mysatellite6``, you would enter the following command::

  # qpc scan add --name myscan --sources mynetwork mysatellite6

Running a Scan
^^^^^^^^^^^^^^
After a scan is created, you can run it. You can run a scan multiple times. Each instance of a scan is assigned a unique identifier, and is known as a scan job.

**IMPORTANT:** Scans run consecutively on the Quipucords server, in the order in which the ``qpc scan start`` command for each scan is entered.

To run a scan, use the following steps:

Run the scan by using the ``scan start`` command, specifying the name of a scan for the ``name`` option::

  # qpc scan start --name scan_name1

For example, if you want to run the scan ``myscan``, you would enter the following command::

  # qpc scan start --name myscan
