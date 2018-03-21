Scanning
--------
Quipucords can scan several types of sources from network systems to vCenter Servers and Satellite servers.

Scanning Lifecycle
^^^^^^^^^^^^^^^^^^
A user defines a scan, see `Working with Scans <working_with_scans.html>`_, and triggers scanning to begin. When the user triggers scanning to begin a scan job is create. When a scan job is created it is queued for processing. Due to the light-weight nature of the Quipucords server scan jobs are run serially. Scan jobs will transition from queued to started and processing will begin. A user can select to pause or cancel a scan job that is pending or running. A paused scan job can be restarted, a canceled scan job cannot. A scan job can halt due to a fatal error resulting in a *failed* status, the status message should help determine the cause of the failure. When a scan results in a *completed* status it produces results that can be viewed in an associated report.

Scan Job Decomposition
^^^^^^^^^^^^^^^^^^^^^^
A Scan Job is broken down into several tasks. If a scan job is performing an inspection several sources, two tasks are created for each source. The first task is a connection task which determines the ability to connect to the source and the number of systems that can be inspected for the defined source. The second task is an inspection task that gathers data from each of the systems. When a scan job is run all the connect tasks for all of the sources will be run prior to the execution of any of the inspection tasks.
