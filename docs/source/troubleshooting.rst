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

  # sudo docker run --name quipucords -d -p 443:443 -e QUIPUCORDS_LOGGING_LEVEL=DEBUG -e DJANGO_LOGGING_LEVEL=DEBUG -v ~/quipucords/sshkeys:/sshkeys -v ~/quipucords/data:/var/data -v ~/quipucords/log:/var/log -i quipucords:0.0.44

If your system does have SELinux enabled, you must append ``:z`` to each volume as follows::

  # sudo docker run --name quipucords -d -p 443:443 -e QUIPUCORDS_LOGGING_LEVEL=DEBUG -e DJANGO_LOGGING_LEVEL=DEBUG -v ~/quipucords/sshkeys:/sshkeys:z -v ~/quipucords/data:/var/data:z -v ~/quipucords/log:/var/log:z -i quipucords:0.0.44

These commands start the server on port ``443`` and map the ``sshkeys``, ``data``, and ``log`` directories to the ``~/quipucords`` home directory for the server with increased logging information.
