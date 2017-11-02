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


class HostCredential(models.Model):
    """The host credential for connecting to host systems via ssh."""

    name = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=1024, null=True)
    sudo_password = models.CharField(max_length=1024, null=True)
    ssh_keyfile = models.CharField(max_length=1024, null=True)
    ssh_passphrase = models.CharField(max_length=1024, null=True)

    def encrypt_fields(self):
        """Encrypt the sensitive fields of the object."""
        if self.password:
            self.password = encrypt_data_as_unicode(self.password)
        if self.sudo_password:
            self.sudo_password = encrypt_data_as_unicode(self.sudo_password)
        if self.ssh_passphrase:
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

    class Meta:
        """Metadata for the model."""

        verbose_name_plural = _(messages.PLURAL_HOST_CREDENTIALS_MSG)
