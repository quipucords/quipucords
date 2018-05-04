.. quipucords documentation master file, created by
   sphinx-quickstart on Thu Feb  1 12:07:29 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Quipucords Documentation
========================

.. text copied from con_about_qpc file, keep in sync

Quipucords, accessed through the ``qpc`` command, is an inspection and reporting tool. It is designed to identify and report environment data, or *facts*, such as the number of physical and virtual systems on a network, their operating systems, and other configuration data. In addition, it is designed to identify and report more detailed facts for some versions of key Red Hat packages and products for the Linux based IT resources in that network.

The ability to inspect the software and systems that are running on your network improves your ability to understand and report on your entitlement usage. Ultimately, this inspection and reporting process is part of the larger system administration task of managing your inventories.

Quipucords requires the configuration of two basic structures to access IT resources and run the inspection process. A *credential* defines user access data such as the user name and password or SSH key of a user with sufficient authority to run the inspection process on a particular source or some of the entities on that source. A *source* defines the entity or entities to be inspected, such as a host, subnet, network, or systems management solution such as vCenter Server or Red Hat Satellite, plus includes one or more credentials to use to access that source during the inspection process. You can save multiple credentials and sources to use with Quipucords in various combinations as you run inspection processes, or *scans*. When you have completed a scan, you can access the collection of facts in the output as a *report* to review the results.

By default, the credentials and sources that are created when using Quipucords are encrypted in a database. The values are encrypted with AES-256 encryption. They are decrypted when the Quipucords server runs a scan, by using a *vault password* to access the encrypted values that are stored in the database.

Quipucords is an *agentless* inspection tool, so there is no need to install the tool on the sources to be inspected.



.. _an_introduction:

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   requirements
   install
   cli_server_interaction
   quick_start
   using_qpc
   Command Line Reference <man>
   troubleshooting
   concepts
