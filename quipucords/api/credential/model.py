#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Defines the models used with the API application.

These models are used in the REST definitions
"""

from django.utils.translation import ugettext as _
from django.db import models
from api.vault import encrypt_data_as_unicode
import api.messages as messages


class Credential(models.Model):
    """The credential for connecting to systems."""

    NETWORK_CRED_TYPE = 'network'
    VCENTER_CRED_TYPE = 'vcenter'
    CRED_TYPE_CHOICES = ((NETWORK_CRED_TYPE, NETWORK_CRED_TYPE),
                         (VCENTER_CRED_TYPE, VCENTER_CRED_TYPE))

    name = models.CharField(max_length=64, unique=True)
    cred_type = models.CharField(
        max_length=9,
        choices=CRED_TYPE_CHOICES,
        null=False
    )
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=1024, null=True)
    sudo_password = models.CharField(max_length=1024, null=True)
    ssh_keyfile = models.CharField(max_length=1024, null=True)
    ssh_passphrase = models.CharField(max_length=1024, null=True)

    @staticmethod
    def is_encrypted(field):
        """Check to see if the password is already encrypted."""
        if '$ANSIBLE_VAULT' in field:
            return True
        return False

    def encrypt_fields(self):
        """Encrypt the sensitive fields of the object."""
        # Uses is_encrypted() to make sure the password/sudo_password/
        # passphrase is not already encrypted, which would be the case
        # in partial_updates that do not update the password
        # (as it grabs the old, encrypted one)
        if self.password and not self.is_encrypted(self.password):
            self.password = encrypt_data_as_unicode(self.password)
        if self.sudo_password and not self.is_encrypted(self.sudo_password):
            self.sudo_password = encrypt_data_as_unicode(self.sudo_password)
        if self.ssh_passphrase and not self.is_encrypted(self.ssh_passphrase):
            self.ssh_passphrase = encrypt_data_as_unicode(self.ssh_passphrase)

    # pylint: disable=arguments-differ
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
