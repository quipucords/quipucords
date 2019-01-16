.. _connection:

Configuring the qpc Command Line Tool Connection
------------------------------------------------

After the Quipucords server is running, you can configure the qpc command line tool to work with the server. When the command line tool is configured, you can log in to Quipucords with the command line interface and begin setting up and running scans on your IT infrastructure.

The ``qpc server config`` command configures the connection between the qpc command line tool and the Quipucords server.

The ``qpc server config`` command takes the following options:

- The ``--host`` option is required. If you are using the qpc command line interface on the same system where the server is running, you can supply the loopback address ``127.0.0.1`` as the value. Otherwise, supply the IP address for your Quipucords server.
- The ``--port`` option is optional. The default value for this option is ``9443``. If you decided to remap the Quipucords default exposed server port to another port, the port option is required. You must supply the port option and the remapped value in the command, for example, ``--port 8443``.

For example, if you are configuring the command line tool on the same system as the server and the server uses the default exposed server port, you would enter the following command to configure the qpc command line tool::

  # qpc server config --host 127.0.0.1

However, if you are configuring the command line tool on a system that is remote from the server, the Quipucords server is running on the IP address 192.0.2.0, and the port is remapped to 8443, you would enter the following command to configure the qpc command line tool::

  # qpc server config --host 192.0.2.0 --port 8443
