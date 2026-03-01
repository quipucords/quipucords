"""EncryptedCharField assures data written/read from the DB is encrypted/decrypted."""

from django.db import models

from api.vault import decrypt_data_as_unicode, encrypt_data_as_unicode


class EncryptedCharField(models.CharField):
    """Class that extends CharField to ensure data is encrypted/decrypted.

    The EncryptedCharField model extends CharField so that it encrypts data
    on save and decrypts data on access using Ansible Vault
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def encrypt_ansible_vault_value(value):
        """Encrypt a value for the Ansible vault if not already encrypted."""
        if "$ANSIBLE_VAULT" in value:
            return value
        return encrypt_data_as_unicode(value)

    def decrypt_value(self, value):
        """Decrypt a value."""
        if "$ANSIBLE_VAULT" in value:
            return decrypt_data_as_unicode(value)
        return value

    def from_db_value(self, value, expression, connection):
        """Decrypt data when retrieved  from the database."""
        if value is None:
            return value
        return self.decrypt_value(value)

    def to_python(self, value):
        """Assure that data is properly decrypted when stored in a Python string."""
        if isinstance(value, str):
            return value
        if value is None:
            return value
        return self.decrypt_value(value)

    def get_prep_value(self, value):
        """Assure that data is properly encrypted before storing in the database."""
        if value is None:
            return value
        if "$ANSIBLE_VAULT" in value:
            value = decrypt_data_as_unicode(value)
        return self.encrypt_ansible_vault_value(value)
