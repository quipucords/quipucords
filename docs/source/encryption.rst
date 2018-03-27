Encryption
----------
Quipucords stores authentication passwords and SSH key passphrases within its database. This sensitive data is encrypted upon creation by using the vault feature of Ansible. For more information, see `Ansible Vault <https://docs.ansible.com/ansible/2.4/vault.html>`_.

Encryption Mechanism
^^^^^^^^^^^^^^^^^^^^
The encryption uses the secret key for the Quipucords server.  The *secret key* for the server is generated during the initial server start process and resides in the directory that is mapped to ``/var/data/``. If you chose the default configuration options for the Quipucords server, the secret key is in the following location: ``~/quipucords/data/secret.txt``.

Data Security
^^^^^^^^^^^^^
Due to the sensitive nature of encryption keys, authentication passwords, and SSH key passphrases, access must be limited for the directory that contains the secret key. Use the security standards for your organization to limit access to this directory.

If you want to choose your own secret key, you can replace the contents of the ``secret.txt`` file. However, you must do this step before storing any data that will be encrypted.
