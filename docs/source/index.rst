.. quipucords documentation master file, created by
   sphinx-quickstart on Thu Feb  1 12:07:29 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Quipucords Documentation
========================

About Quipucords
````````````````
Quipucords, accessed through the ``qpc`` command, is an inspection and reporting tool. It is designed to identify and report environment data, or *facts*, such as the number of physical and virtual systems on a network, their operating systems, and other configuration data. In addition, it is designed to identify and report more detailed facts for some versions of key Red Hat packages and products for the Linux based IT resources in that network.

The ability to inspect the software and systems that are running on your network improves your ability to understand and report on your entitlement usage. Ultimately, this inspection and reporting process is part of the larger system administration task of managing your inventories.

Quipucords requires two types of data to access IT resources and run the inspection process. A *credential* defines user information such as the user name and password or SSH key of the user that runs the inspection process. A *source* defines the entity to be inspected, such as a host, subnet, network, or systems management solution such as vCenter Server or Red Hat Satellite, plus includes one or more credentials to use to access that network or systems management solution during the inspection process. You can save multiple credentials and sources to use with Quipucords in various combinations as you run inspection processes, or *scans*. When you have completed a scan, you can access the output as a *report* to review the results.


.. _an_introduction:

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   requirements
   install
   quick_start
   cli_server_interaction
   working_with_sources
   working_with_scans
   working_with_scan_jobs
   working_with_reports
   Command Line Usage <man>
   troubleshooting
   concepts
