Requirements
============
Before installing Quipucords in your environment, review the following guidelines about installing and running Quipucords:

- You must install Quipucords on a system that is running Red Hat Enterprise Linux 6 or 7, CentOS 7, or Fedora 27 or 28. For an installation on Fedora, the scripted installation of Quipucords might not work correctly on all systems. Therefore, the best practice for a Fedora installation is to use the step-by-step installation instructions.
- The system that Quipucords is installed on must have access to the systems to be discovered and inspected.
- Any network sources that are targeted for the inspection process must be running SSH.
- For a scan of network systems, the user account (credential) that Quipucords uses for the SSH connection into the target systems must have adequate permissions to run commands and read certain files on those systems. For example, some of the commands require privilege elevation to gather the complete set of facts for the scan. For more information about these commands, see `Commands Used in Scans of Remote Network Assets <commands.html>`_
- The credential user account requires an ``sh`` shell or a similar shell. For example, the shell *cannot* be the ``/sbin/nologin`` or ``/bin/false`` shell.
