Configuring and Starting Quipucords
===================================
After you install the Quipucords server container image in the image registry, you must select configuration options to be used at the time that you start the server and the command line tool. When you are sure of the options that you want to use, you can start Quipucords by starting the server and the command line tool.

Selecting the Quipucords Server Configuration Options
-----------------------------------------------------
When you run the command to start the Quipucords server, you supply values for several options that affect the configuration of that server. You must make the following decisions:

- Accepting or changing the default exposed server port
- Selecting a directory for SSH keys
- Selecting a directory for the SQLlite database
- Selecting a directory for log output

The following steps guide you through those choices.

1. Accept or change the default exposed server port to use for HTTPS communication. By default, the server exposes port 443, which is the standard HTTPS port. You can choose to use that port or remap the port to be used on your server.

   - If you select to expose port 443, you would use the following option when you run the Docker command to start the server: ``-p 443:443``.
   - If you want to remap the port on your system, you would supply a new value for the port when you run the Docker command to start the server. The syntax of this option is  ``-p <host_port>:<container_port>``. For example, to remap the port to ``8443``, you would enter the followng option in the command: ``-p 8443:443``. Additionally, Docker supplies an option to select a free port for all exposed ports by using the ``-P`` option; the port mapping is then available from the ``sudo docker ps`` command.

2. Select values for the directory for SSH keys, the directory for the SQLlite database, and the directory for the log output. The most efficient way to configure these options is to create a home directory for the Quipucords server and then use that home directory for each of thse three options.

   \a. Create the home directory. The following example command creates the home directory  ``~/quipucords``:

    ``# mkdir -p ~/quipucords``

   \b. Change to that home directory. For example:

    ``# cd ~/quipucords``

   \c. Create subdirectories to house the SSH keys, (``~/quipucords/sshkeys``), database (``~/quipucords/data``), and log output (``~/quipucords/log``). For example::

       # mkdir sshkeys
       # mkdir data
       # mkdir log

Starting the Quipucords Server
------------------------------
After you make the decisions on the configuration options for the server, you can start the Quipucords server. The following commands assume that you used the default port and the recommended steps to create a home directory and subdirectories for the SSH keys, SQLlite database, and log output during the Quipucords server configuration.

If your system does not have SELinux enabled, you can start the Quipucords server with the following Docker command::

  # sudo docker run --name quipucords -d -p 443:443 -v ~/quipucords/sshkeys:/sshkeys -v ~/quipucords/data:/var/data -v ~/quipucords/log:/var/log -i quipucords:1.0.0

If your system does have SELinux enabled, you must append ``:z`` to each volume as follows::

  # sudo docker run --name quipucords -d -p 443:443 -v ~/quipucords/sshkeys:/sshkeys:z -v ~/quipucords/data:/var/data:z -v ~/quipucords/log:/var/log:z -i quipucords:1.0.0

These commands start the server on port ``443`` and map the ``sshkeys``, ``data``, and ``log`` directories to the ``~/quipucords`` home directory for the server.

To view the status of the server after it is running, enter the following command::

  # docker ps

Changing the Default Password for the Quipucords Server
-------------------------------------------------------
The Quipucords server has a default administrator user with a default user name of ``admin`` and a default password of ``pass``. To ensure the security of your Quipucords server, it is recommended that you change the default password to a different password.

To change the default password for the Quipucords server, use the following steps:

1. In a browser window, enter the URL to the Quipucords server. When you enter the URL to the Quipucords server, the browser loads a web page that shows an administrative login dialog box.

   - If the browser window is running on the same system as the server and you used the default port of ``443`` for the server, the URL is ``https://localhost/admin``.
   - If the browser window is running on a remote system, or if it is on the same system but you changed the default HTTPS port, enter the URL in the following format: ``https://ip_address:port/admin``. For example, if the IP address for the server is 192.0.2.0 and the port is remapped to ``8443``, you would enter ``https://192.0.2.0:8443/admin`` in the browser window.

2. In the resulting web page that contains the Quipucords administrative login dialog box, enter the default user name ``admin`` and the default password ``pass`` to log in to the Quipucords server.

3. Click **Change password** to enter a new password for the Quipucords server. Record the new password in an enterprise password management solution or other password management tool, as determined by the best practices for your organization.

**TIP:** You can also enter the local or remote URL (as applicable) for the Quipucords server in a browser window to verify that the Quipucords server is responding.

.. _connection:

Configuring the qpc Command Line Tool Connection
------------------------------------------------
After the Quipucords server is running, you can configure the qpc command line tool to work with the server. The ``qpc server config`` command configures the connection between the qpc command line tool and the Quipucords server.

The ``qpc server config`` command takes the following options:

- The ``--host`` option is required. If you are using the qpc command line tool on the same system where the server is running, you can supply the loopback address ``127.0.0.1`` as the value. Otherwise, supply the IP address for your Quipucords server.
- The ``--port`` option is optional. The default value for this option is ``443``. If you decided to remap the Quipucords default exposed server port to another port, the port option is required. You must supply the port option and the remapped value in the command, for example, ``--port 8443``.

For example, if you are configuring the command line tool on the same system as the server and the server uses the default exposed server port, you would enter the following command to configure the qpc command line tool:

  ``# qpc server config --host 127.0.0.1``

However, if you are configuring the command line tool on a system that is remote from the server, the Quipucords server is running on the IP address 192.0.2.0, and the port is remapped to 8443, you would enter the following command to configure the qpc command line tool:

  ``# qpc server config --host 192.0.2.0 --port 8443``

.. _login:

Logging in to and Logging out of the qpc Command Line Interface
---------------------------------------------------------------
After the connection between the qpc command line tool and the Quipcords server is configured on the system where you want to use the qpc command line interface, you can log in to the interface and begin using it to run qpc commands.

To log in to the qpc command line interface, enter the following command:

  ``# qpc server login``

The ``qpc server login`` command retrieves a token that is used for authentication with subsequent command line interface commands. That token is removed when you log out of the server. To log out of the server, enter the following command:

  ``# qpc server logout``
