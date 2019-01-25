Troubleshooting
===============
The following sections provide a reference for viewing logging information from the command line and server to enable troubleshooting of various activities being performed with Quipucords.

Troubleshooting the Command Line
--------------------------------
Logs for the command line can be found in the ``~/.local/share/qpc/`` directory with the name **qpc.log**. Logging information is captured for each command with the input arguments and request endpoint and response information to enable situational debugging. The command line supports a global flag ``-v`` to increase verbosity of the logs.

Troubleshooting the Server
--------------------------
Logs from the server are mapped from the running container into a users specified directory. If you used the defaults found in the `Selecting the Quipucords Server Configuration Options <configure.html#selecting-the-quipucords-server-configuration-options>`_ section, the directory would be ``~/quipucords/log``. You will find three log files within this directory:

- **supervisord.log**
  - Logs for the supervisor service that keeps the server running in case of unexpected issues
- **quipucords.log**
  - Logs for server workers
- **app.log**
  - Server logs for main application

Default logging levels for the server can be altered by setting logging environment variables to **DEBUG**:

- QUIPUCORDS_LOGGING_LEVEL
  - Application logging
- DJANGO_LOGGING_LEVEL
  - Infrastructure logging

If your system does not have SELinux enabled, you can start the Quipucords server with the following Docker command with increased logging::

  # sudo docker run --name quipucords -d -p 9443:443 -e QUIPUCORDS_LOGGING_LEVEL=DEBUG -e DJANGO_LOGGING_LEVEL=DEBUG -v ~/quipucords/sshkeys:/sshkeys -v ~/quipucords/data:/var/data -v ~/quipucords/log:/var/log -i quipucords:0.0.47

If your system does have SELinux enabled, you must append ``:z`` to each volume as follows::

  # sudo docker run --name quipucords -d -p 9443:443 -e QUIPUCORDS_LOGGING_LEVEL=DEBUG -e DJANGO_LOGGING_LEVEL=DEBUG -v ~/quipucords/sshkeys:/sshkeys:z -v ~/quipucords/data:/var/data:z -v ~/quipucords/log:/var/log:z -i quipucords:0.0.47

These commands start the server on port ``9443`` and map the ``sshkeys``, ``data``, and ``log`` directories to the ``~/quipucords`` home directory for the server with increased logging information.

Cleaning out the Database
-------------------------
Our command to run a postgres container does implement docker volumes. Volumes allow our postgres data to be persistent, which means that the data will remain even if the postgres container is removed and recreated. If for any reason you would like to delete your postgres database, you will need to remove the docker volume.

Removing the volume for RHEL 6 or Centos 6

# rm -rf /var/lib/docker/volumes/qpc-data

Removing the volume for RHEL 7, Centos 7, Fedora 27, or Fedora 28

# docker volume rm qpc-data

Adding CLI Inputs with Backslashes
----------------------------------
A single backslash is used as an escape character in both Shell and Python, which can cause undesired values if only one backslash is present. Therefore, CLI inputs containing a backslash will need to be escaped with another backslash ``\\``. For example if you wanted to add a credential with the username ``Domain\Username``, the value would have to be escaped::

    # qpc cred add --type vcenter --name ActiveDirectory --username Domain\\Username --password
