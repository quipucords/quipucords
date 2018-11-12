Working with Insights
---------------------
In order to use Quipucords to upload data to Red Hat Insights, the Insights client must be installed. To install and setup the Insights client, visit https://access.redhat.com/products/red-hat-insights#getstarted and follow the instructions.


Uploading To Insights
^^^^^^^^^^^^^^^^^^^^^
Use the ``qpc insights upload`` command to upload a deployments report to Red Hat Insights. You can upload a report to Insights using the associated report identifier or scan job identifier for the scan that is used to generate the report::

  qpc insights upload (--scan-job scan_job_identifier | --report report_identifier )

For example, to create and upload the deployments report with a report identifier of ``1``, you would enter the following command::

  qpc insights upload --report 1
