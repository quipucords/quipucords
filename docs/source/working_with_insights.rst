Working with Insights
---------------------
If you would like to use Quipucords to upload data to Red Hat Insights, some additional external setup is required. The qpc commands related to Insights expect the Insights client to be installed. More information about setting up the Insights client can be found here: https://access.redhat.com/products/red-hat-insights#getstarted.


Uploading To Insights
^^^^^^^^^^^^^^^^^^^^^
When a scan completes, it returns a report identifier that can then be used to upload a deployments report to Insights. The deployments report process runs steps to merge the facts found during the inspection of various hosts that are contacted during the scan. To generate and upload a deployments report to insights, run the ``qpc insights upload`` command and specify the report identifier.

For example, to create and upload the deployments report for a scan with report identifier ``1``, you would enter the following command::

  # qpc insights upload --report 1
