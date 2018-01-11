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

"""Models system fingerprints."""

from django.db import models
from api.fact.model import FactCollection
from api.source.model import Source


class SystemFingerprint(models.Model):
    """Represents system fingerprint."""

    INFRASTRUCTURE_TYPE = (
        ('bare_metal', 'Bare Metal'), ('virtualized',
                                       'Virtualized'), ('unknown', 'Unknown')
    )

    fact_collection_id = models.ForeignKey(FactCollection,
                                           models.CASCADE)
    source_id = models.ForeignKey(Source, models.CASCADE)

    os_name = models.CharField(max_length=64, unique=False)
    os_release = models.CharField(max_length=128, unique=False)
    os_version = models.CharField(max_length=64, unique=False)

    bios_uuid = models.CharField(max_length=36, unique=False)
    subscription_manager_id = models.CharField(max_length=36, unique=False)

    connection_host = models.CharField(
        max_length=256, unique=False, blank=True, null=True)
    connection_port = models.PositiveIntegerField(unique=False, null=True)
    connection_uuid = models.UUIDField(unique=False)

    cpu_count = models.PositiveIntegerField(unique=False, null=True)
    cpu_core_per_socket = models.PositiveIntegerField(unique=False, null=True)
    cpu_siblings = models.PositiveIntegerField(unique=False, null=True)
    cpu_hyperthreading = models.NullBooleanField()
    cpu_socket_count = models.PositiveIntegerField(unique=False, null=True)
    cpu_core_count = models.PositiveIntegerField(unique=False, null=True)

    system_creation_date = models.DateField(null=True)
    infrastructure_type = models.CharField(
        max_length=10, choices=INFRASTRUCTURE_TYPE)

    virtualized_is_guest = models.NullBooleanField()
    virtualized_type = models.CharField(max_length=64, unique=False, null=True)
    virtualized_num_guests = models.PositiveIntegerField(
        unique=False, null=True)
    virtualized_num_running_guests = models.PositiveIntegerField(
        unique=False, null=True)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'fact_collection:{}, ' \
            'connection_host:{} '\
            'connection_port:{} '\
            'connection_uuid:{} '\
            'cpu_count:{} '\
            'cpu_core_per_socket:{} '\
            'cpu_siblings:{} '\
            'cpu_hyperthreading:{} '\
            'cpu_socket_count:{} '\
            'cpu_core_count:{} '\
            'system_creation_date:{} '\
            'infrastructure_type:{} '\
            'os_name:{}, '\
            'os_version:{}, '\
            'os_release:{}, '\
            'virtualized_is_guest:{} '\
            'virtualized_type:{} '\
            'virtualized_num_guests:{} '\
            'virtualized_num_running_guests:{} '\
            .format(self.id,
                    self.fact_collection_id.id,
                    self.connection_host,
                    self.connection_port,
                    self.connection_uuid,
                    self.cpu_count,
                    self.cpu_core_per_socket,
                    self.cpu_siblings,
                    self.cpu_hyperthreading,
                    self.cpu_socket_count,
                    self.cpu_core_count,
                    self.system_creation_date,
                    self.infrastructure_type,
                    self.os_name,
                    self.os_version,
                    self.os_release,
                    self.virtualized_is_guest,
                    self.virtualized_type,
                    self.virtualized_num_guests,
                    self.virtualized_num_running_guests) + '}'
