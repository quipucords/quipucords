"""Defines the models used with the API application.

These models are used in the REST definitions
"""
from django.db import models
from django.utils.translation import gettext as _

from api import messages
from api.vault import encrypt_data_as_unicode
from constants import DataSources


class Credential(models.Model):
    """The credential for connecting to systems."""

    BECOME_USER_DEFAULT = "root"
    BECOME_SUDO = "sudo"
    BECOME_SU = "su"
    BECOME_PBRUN = "pbrun"
    BECOME_PFEXEC = "pfexec"
    BECOME_DOAS = "doas"
    BECOME_DZDO = "dzdo"
    BECOME_KSU = "ksu"
    BECOME_RUNAS = "runas"
    BECOME_METHOD_CHOICES = (
        (BECOME_SUDO, BECOME_SUDO),
        (BECOME_SU, BECOME_SU),
        (BECOME_PBRUN, BECOME_PBRUN),
        (BECOME_PFEXEC, BECOME_PFEXEC),
        (BECOME_DOAS, BECOME_DOAS),
        (BECOME_DZDO, BECOME_DZDO),
        (BECOME_KSU, BECOME_KSU),
        (BECOME_RUNAS, BECOME_RUNAS),
    )

    name = models.CharField(max_length=64, unique=True)
    cred_type = models.CharField(max_length=9, choices=DataSources.choices, null=False)
    # Important note: we allow `null=True` and `blank=True` for most of the fields
    # because this model is overloaded, conditionally expecting values in some fields
    # but not others based on cred_type and other runtime conditions. Input validation
    # exists elsewhere to enforce not-blank values in specific fields when applicable.
    # Future refactoring idea: implement different credential types in separate models.
    username = models.CharField(max_length=64, null=True, blank=True)
    password = models.CharField(max_length=1024, null=True, blank=True)
    auth_token = models.CharField(max_length=6000, null=True, blank=True)
    ssh_keyfile = models.CharField(max_length=1024, null=True, blank=True)
    ssh_key = models.CharField(max_length=65536, null=True, blank=True)
    ssh_passphrase = models.CharField(max_length=1024, null=True, blank=True)
    become_method = models.CharField(
        max_length=6, choices=BECOME_METHOD_CHOICES, null=True, blank=True
    )
    become_user = models.CharField(max_length=64, null=True, blank=True)
    become_password = models.CharField(max_length=1024, null=True, blank=True)

    ENCRYPTED_FIELDS = [
        "password",
        "ssh_passphrase",
        "ssh_key",
        "become_password",
        "auth_token",
    ]

    @staticmethod
    def is_encrypted(field):
        """Check to see if the password is already encrypted."""
        if "$ANSIBLE_VAULT" in field:
            return True
        return False

    def encrypt_fields(self):
        """Encrypt the sensitive fields of the object."""
        # Uses is_encrypted() to make sure the password/become_password/
        # passphrase is not already encrypted, which would be the case
        # in partial_updates that do not update the password
        # (as it grabs the old, encrypted one)
        for field_name in self.ENCRYPTED_FIELDS:
            field_value = getattr(self, field_name, None)
            if field_value and not self.is_encrypted(field_value):
                encrypted_value = encrypt_data_as_unicode(field_value)
                setattr(self, field_name, encrypted_value)

    def save(self, *args, **kwargs):
        """Save the model object."""
        self.encrypt_fields()
        super().save(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update the model object."""
        self.encrypt_fields()
        super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Update the model object."""
        self.encrypt_fields()
        super().partial_update(request, *args, **kwargs)

    class Meta:
        """Metadata for the model."""

        verbose_name_plural = _(messages.PLURAL_HOST_CREDENTIALS_MSG)
