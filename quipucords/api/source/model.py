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
from api.credential.model import Credential


class Source(models.Model):
    """A source connects a list of credentials and a list of hosts."""

    name = models.CharField(max_length=64, unique=True)
    ssh_port = models.IntegerField(default=22)
    credentials = models.ManyToManyField(Credential)
    # Source also has the field hosts, which is created by the
    # ForeignKey in HostRange below.

    def __str__(self):
        """Convert to string."""
        return '{ id:%s, name:%s }' % (self.id, self.name)


class HostRange(models.Model):
    """A HostRange is a subset of a source to scan.

    It can be either an IP range or a DNS name range. A HostRange is
    not the same as a set of hosts because there may be parts of the
    IP or DNS range that don't correspond to any host, but we still
    need to remember them because in the future there could be hosts
    there.
    """

    # HostRanges provide a convenient way for a Source to
    # store a list of name ranges.  As of now we don't make any effort
    # to deduplicate when different Sources have overlapping
    # (or identical) ranges. If we ever want to show the user exactly
    # what parts of their source are being scanned, we will have to
    # dedup.

    # host_range is an IP address range or a DNS name range in Ansible
    # format.
    host_range = models.CharField(max_length=1024)
    source = models.ForeignKey(Source,
                               models.CASCADE,
                               related_name='hosts')
