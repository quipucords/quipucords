Encryption
----------
Quipucords stores authentication passwords and SSH key passphrases within its database. This sensitive data is encrypted upon creation using the `Ansible Vault <https://docs.ansible.com/ansible/2.4/vault.html>`_.

Encryption Mechanism
^^^^^^^^^^^^^^^^^^^^
The encryption utilizes the *secret key* for the server.  The *secret key* for the server is generated during the initial server startup and resides in the directory mapped to ``/var/data/``, if you chose the defaults from the installation section it can be found in the ``~/quipucords/data/secret.txt``.

Data Security
^^^^^^^^^^^^^
Due to the sensitive data access should be limited to this mapped directory. If you wish to choose your *secret key* you can replace the content of the ``secret.txt``, but you must do so before storing any data that will be encrypted.
