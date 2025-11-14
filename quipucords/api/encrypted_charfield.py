"""EncryptedCharField assures data written/read from the DB is encrypted/decrypted."""

from django.db import models

from api.hashivault import HashiVault
from api.vault import decrypt_data_as_unicode, encrypt_data_as_unicode


class EncryptedCharField(models.CharField):
    """
    The EncryptedCharField model extends CharField so that it encrypts data
    on save and decrypts data on access using either Ansible Vault (default)
    or optionally a HashiCorp Vault.
    """
    def __init__(self, *args, **kwargs):
        self.hashi_vault = HashiVault()
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if self.hashi_vault.client:
            return self.hashi_vault.client.decrypt(value)
        return decrypt_data_as_unicode(value)

    def to_python(self, value):
        if isinstance(value, str):
            return value
        if value is None:
            return value
        if self.hashi_vault.client:
            return self.hashi_vault.client.decrypt(value)
        return decrypt_data_as_unicode(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        if self.hashi_vault.client:
            return self.hashi_vault.client.encrypt(value)
        return encrypt_data_as_unicode(value)
