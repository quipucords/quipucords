Working with Scans
==================
Scans compose sources to be scanned in a reproducible way. The sections below will describe how they are created and how to start a scan.

Creating a Scan
---------------
After you set up your credentials and sources, you can run a Quipucords scan to inspect your IT environment. You can create a scan on a single source or combine sources, even sources of different types.

To create a scan, use the following steps:

Create the scan by using the ``scan add`` command, specifying a name for the ``name`` option and one or more sources for the ``sources`` option::

  # qpc scan add --name scan1 --sources source_name1 source_name2

For example, if you want to create a scan called ``myscan`` with the network source ``mynetwork`` and the Satellite source ``mysatellite6``, you would enter the following command::

  # qpc scan add --name myscan --sources mynetwork mysatellite6

Running a Scan
--------------

**IMPORTANT:** Scans run consecutively on the Quipucords server, in the order in which the ``qpc scan start`` command for each scan is entered.

To run a scan, use the following steps:

Run the scan by using the ``scan start`` command, specifying the name of a scan for the ``name`` option::

  # qpc scan start --name scan_name1

For example, if you want to run the scan ``myscan``, you would enter the following command::

  # qpc scan start --name myscan
