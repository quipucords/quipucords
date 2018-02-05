#
# Copyright (c) 2017-2018 Red Hat, Inc.
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

import json
from django.db import models
from api.credential.model import Credential


class SourceOptions(models.Model):
    """The source options allows configuration of a sources."""

    SATELLITE_VERSION_5 = '5'
    SATELLITE_VERSION_62 = '6.2'
    SATELLITE_VERSION_63 = '6.3'
    SATELLITE_VERSION_CHOICES = ((SATELLITE_VERSION_62, SATELLITE_VERSION_62),
                                 (SATELLITE_VERSION_63, SATELLITE_VERSION_63),
                                 (SATELLITE_VERSION_5, SATELLITE_VERSION_5))

    satellite_version = models.CharField(
        max_length=10,
        choices=SATELLITE_VERSION_CHOICES,
        null=False,
        default=SATELLITE_VERSION_62
    )

    ssl_cert_verify = models.NullBooleanField()

    def __str__(self):
        """Convert to string."""
        return '{ id:%s, satellite_version:%s, ssl_cert_verify:%s}' %\
            (self.id, self.satellite_version, self.ssl_cert_verify)


class Source(models.Model):
    """A source connects a list of credentials and a list of hosts."""

    NETWORK_SOURCE_TYPE = 'network'
    VCENTER_SOURCE_TYPE = 'vcenter'
    SATELLITE_SOURCE_TYPE = 'satellite'
    SOURCE_TYPE_CHOICES = ((NETWORK_SOURCE_TYPE, NETWORK_SOURCE_TYPE),
                           (VCENTER_SOURCE_TYPE, VCENTER_SOURCE_TYPE),
                           (SATELLITE_SOURCE_TYPE, SATELLITE_SOURCE_TYPE))

    name = models.CharField(max_length=64, unique=True)
    source_type = models.CharField(
        max_length=7,
        choices=SOURCE_TYPE_CHOICES,
        null=False
    )
    port = models.IntegerField(null=True)
    options = models.ForeignKey(
        SourceOptions, null=True, on_delete=models.CASCADE)
    credentials = models.ManyToManyField(Credential)
    hosts = models.TextField(unique=False, null=False)

    def __str__(self):
        """Convert to string."""
        return '{ id:%s, name:%s, type:%s}' %\
            (self.id, self.name, self.source_type)

    def get_hosts(self):
        """Access hosts as python list instead of str.

        :returns: host as a python list
        """
        return json.loads(self.hosts)
