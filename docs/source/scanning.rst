Scans and Scan Jobs
-------------------
Quipucords can scan several types of sources. These include network systems, vCenter Server servers, and Satellite servers.

You create a scan by providing a name for the scan and the sources to be scanned. You then start the scan, either immediately or at a later time by referencing the saved scan. For more information about these steps, see `Working with Scans <working_with_scans.html>`_.

Scan Job Lifecycle
^^^^^^^^^^^^^^^^^^
An individual instance of a scan, or *scan job*, moves through several states during its lifecycle.

When you start a scan, a scan job is created and the scan job is in the *created* state. The scan job is then queued for processing and the scan job transitions to the *pending* state. Due to the lightweight nature of the Quipucords server, scan jobs run serially.

As the Quipucords server reaches a specific scan job in the queue, that scan job transitions from the *pending* state to the *running* state as the processing of that scan job begins. If the scan process completes successfully, the scan job transitions to the *completed* state and the scan job produces results that can be viewed in a report. If the scan process results in a fatal error that prevents successful completion of the scan, the scan job halts and the scan job transitions to the *failed* state. An additional status message for the failed scan contains information to help determine the cause of the failure.

Other states for a scan job result from user action that is taken on the scan job. You can pause or cancel a scan job while it is pending or running. A scan job in the *paused* state can be restarted. A scan job in the *canceled* state cannot be restarted.

Scan Job Tasks
^^^^^^^^^^^^^^
A scan job moves through two phases, or tasks. The first task is a *connection task* that determines the ability to connect to the source and finds the number of systems that can be inspected for the defined source. The second task is an *inspection task* that gathers data from each of the systems in the defined source to output the scan results.

If the scan is configured so that it contains several sources, then when the scan job runs, these two tasks are created for each source. First, all of the connection tasks for all of the sources run to establish connections to the sources and find the systems that can be inspected. Then all of the inspection tasks for all of the sources run to inspect the contents of the systems that are contained in the sources.

Scan Job Processing
^^^^^^^^^^^^^^^^^^^
When the scan job runs the connection task for a source, it attempts to connect to the network, server for vCenter Server, or server for Satellite. If the connection to vCenter Server or Satellite fails, then the connection task fails. For a network scan, if the network is not reachable or the credentials are invalid, the connection task reports zero (0) successful systems. If only some of the systems for a network scan are reachable, the connection task reports success on the systems that are reachable, and the connection task does not fail.

When the scan job runs the inspection task for a source, it checks the state of the connection task. If the connection task shows a failed state or if there are zero (0) successful connections, the scan job transitions to the failed state. However, if the connection task reports at least one successful connection, the inspection task continues. The results for the scan job then show success and failure data for each individual system. If the inspection task is not able to gather results from the successful systems, or if another unexpected error occurs during the inspection task, then the scan job transitions to the failed state.

If a scan contains multiple sources, each source has its own connection and inspection tasks. These tasks are processed independently from the tasks for the other sources. If any task for any of the sources fails, the scan job transitions to the failed state. The scan job transitions to the completed state only if all scan job tasks for all sources complete successfully.
