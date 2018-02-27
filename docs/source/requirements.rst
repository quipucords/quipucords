Requirements
============
Before installing Quipucords in your environment, review the following guidelines about installing and running Quipucords:

- You must install Quipucords on a system that is running Red Hat Enterprise Linux 6 or 7.
- The system that Quipucords is installed on must have access to the systems to be discovered and inspected.
- The systems that are targeted for the inspection process must be running SSH.
- The user account that Quipucords uses for the SSH connection into the target systems, otherwise known as the credential, must have adequate permissions to run commands and read certain files, such as privilege escalation required for the ``systemctl`` command.
- The credential user account requires an sh shell or a similar shell. For example, the shell *cannot* be a /sbin/nologin or /bin/false shell.
