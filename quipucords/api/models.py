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

from django.db import models
from api.vault import encrypt_data_as_unicode


class Credential(models.Model):
    """The base credential model, all of which will have a name"""
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name_plural = 'Credentials'


class HostCredential(Credential):
    """The host credential for connecting to host systems via ssh"""
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=1024, null=True)
    sudo_password = models.CharField(max_length=1024, null=True)
    ssh_keyfile = models.CharField(max_length=1024, null=True)

    def encrypt_fields(self):
        """Encrypt the sensitive fields of the object"""
        if self.password:
            self.password = encrypt_data_as_unicode(self.password)
        if self.sudo_password:
            self.sudo_password = encrypt_data_as_unicode(self.sudo_password)

    # pylint: disable=arguments-differ
    def save(self, *args, **kwargs):
        """Save the model object
        """
        self.encrypt_fields()
        super().save(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update the model object
        """
        self.encrypt_fields()
        super().update(request, *args, **kwargs)

    class Meta:
        verbose_name_plural = 'Host Credentials'


class NetworkProfile(models.Model):
    """A network profile connects a list of credentials and a list of hosts."""
    name = models.CharField(max_length=64, unique=True)
    # Comma-separated list of host specifiers
    hosts = models.CharField(max_length=1024)
    ssh_port = models.IntegerField()
    # Comma-separated list of credential names. We identify
    # credentials by name, not ID, to support the behavior where a
    # user creates a credential of a given name, deletes it, and makes
    # a new one of the same name.
    credentials = models.CharField(max_length=1024)
