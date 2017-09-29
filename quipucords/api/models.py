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
    ssh_port = models.IntegerField()
    credential_ids = models.ManyToManyField(HostCredential)
    # NetworkProfile also has the field hosts, which is created by the
    # ForeignKey in HostRange below.


class HostRange(models.Model):
    """A HostRange is a subset of a network to scan.

    It can be either an IP range or a DNS name range. A HostRange is
    not the same as a set of hosts because there may be parts of the
    IP or DNS range that don't correspond to any host, but we still
    need to remember them because in the future there could be hosts
    there.
    """

    # HostRanges provide a convenient way for a NetworkProfile to
    # store a list of name ranges.  As of now we don't make any effort
    # to deduplicate when different NetworkProfiles have overlapping
    # (or identical) ranges. If we ever want to show the user exactly
    # what parts of their network are being scanned, we will have to
    # dedup.

    # host_range is an IP address range or a DNS name range in Ansible
    # format.
    host_range = models.CharField(max_length=1024)
    network_profile = models.ForeignKey(NetworkProfile,
                                        models.CASCADE,
                                        related_name='hosts')
