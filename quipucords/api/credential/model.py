"""Defines the models used with the API application.

These models are used in the REST definitions
"""
from django.db import models
from django.utils.translation import gettext as _

from api import messages
from api.vault import encrypt_data_as_unicode


class Credential(models.Model):
    """The credential for connecting to systems."""

    NETWORK_CRED_TYPE = "network"
    VCENTER_CRED_TYPE = "vcenter"
    SATELLITE_CRED_TYPE = "satellite"
    OPENSHIFT_CRED_TYPE = "openshift"
    CRED_TYPE_CHOICES = (
        (NETWORK_CRED_TYPE, NETWORK_CRED_TYPE),
        (VCENTER_CRED_TYPE, VCENTER_CRED_TYPE),
        (SATELLITE_CRED_TYPE, SATELLITE_CRED_TYPE),
        (OPENSHIFT_CRED_TYPE, OPENSHIFT_CRED_TYPE),
    )
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
    cred_type = models.CharField(max_length=9, choices=CRED_TYPE_CHOICES, null=False)
    username = models.CharField(max_length=64, null=True)
    password = models.CharField(max_length=1024, null=True)
    auth_token = models.CharField(max_length=1024, null=True)
    ssh_keyfile = models.CharField(max_length=1024, null=True)
    ssh_passphrase = models.CharField(max_length=1024, null=True)
    become_method = models.CharField(
        max_length=6, choices=BECOME_METHOD_CHOICES, null=True
    )
    become_user = models.CharField(max_length=64, null=True)
    become_password = models.CharField(max_length=1024, null=True)

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
        if self.password and not self.is_encrypted(self.password):
            self.password = encrypt_data_as_unicode(self.password)
        if self.ssh_passphrase and not self.is_encrypted(self.ssh_passphrase):
            self.ssh_passphrase = encrypt_data_as_unicode(self.ssh_passphrase)
        if self.become_password and not self.is_encrypted(self.become_password):
            self.become_password = encrypt_data_as_unicode(self.become_password)
        if self.auth_token and not self.is_encrypted(self.auth_token):
            self.auth_token = encrypt_data_as_unicode(self.auth_token)

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        """Save the model object."""
        self.encrypt_fields()
        super().save(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update the model object."""
        self.encrypt_fields()
        # pylint:disable=no-member
        super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Update the model object."""
        self.encrypt_fields()
        # pylint:disable=no-member
        super().partial_update(request, *args, **kwargs)

    class Meta:
        """Metadata for the model."""

        verbose_name_plural = _(messages.PLURAL_HOST_CREDENTIALS_MSG)
