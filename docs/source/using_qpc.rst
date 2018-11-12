Using Quipucords from the Command Line Interface
================================================
After you use the command line interface to log in to the Quipucords server, you can begin using Quipucords.

You use the capabilities of Quipucords to inspect and gather information on your IT infrastructure. Quipucords requires the configuration of two basic structures to manage the inspection process. A *credential* contains the access credentials, such as the user name and password or SSH key of the user, with sufficient authority to run the inspection process on a particular source. For more information about this authority, see `Requirements <requirements.html>`_. A *source* defines the entity or entities to be inspected, such as a host, subnet, network, or systems management solution such as vCenter Server or Satellite. When you create a source, you also include one or more of the configured credentials to use to access the individual entities in the source during the inspection process.

You can save multiple credentials and sources to use with Quipucords in various combinations as you run inspection processes, or *scans*. A scan can be run multiple times, and each instance is saved as a *scan job*. When you have completed a scan, you can access the collection of *facts* in the scan job output as a *report* to review the results.


.. include:: working_with_sources.rst

.. include:: working_with_scans.rst

.. include:: working_with_scan_jobs.rst

.. include:: working_with_reports.rst

.. include:: working_with_insights.rst
