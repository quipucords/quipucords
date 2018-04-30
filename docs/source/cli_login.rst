.. _login:

Logging in to the Quipucords Server
-----------------------------------

After the connection between the qpc command line tool and the Quipucords server is configured on the system where you want to use the command line interface, you can log into the server and begin using the command line interface to run the qpc commands that set up and run scans.

1. To log in to the server, enter the following command::

    # qpc server login

2. Enter the server user name and password at the prompts.  The default login is ``admin`` and the password is ``pass``.

The ``qpc server login`` command retrieves a token that is used for authentication with subsequent command line interface commands. That token is removed when you log out of the server, and expires daily.
