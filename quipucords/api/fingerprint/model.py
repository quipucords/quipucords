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

"""Models system fingerprints."""

from django.db import models
from api.fact.model import FactCollection


class SystemFingerprint(models.Model):
    """Represents system fingerprint."""

    SOURCE_TYPE = (
        ('network', 'Ansible'),
        ('vcenter', 'VCenter'),
        ('unknown', 'Unknown')
    )

    INFRASTRUCTURE_TYPE = (
        ('bare_metal', 'Bare Metal'),
        ('virtualized', 'Virtualized'),
        ('unknown', 'Unknown')
    )

    # Scan information
    report_id = models.ForeignKey(FactCollection, models.CASCADE)

    # Common facts
    name = models.CharField(max_length=256, unique=False, null=True)
    os_name = models.CharField(max_length=64, unique=False)
    os_release = models.CharField(
        max_length=128, unique=False, default='unknown')
    os_version = models.CharField(max_length=64, unique=False, null=True)

    infrastructure_type = models.CharField(
        max_length=10, choices=INFRASTRUCTURE_TYPE, default='unknown')
    virtualized_is_guest = models.NullBooleanField()

    mac_addresses = models.TextField(unique=False, null=True)
    ip_addresses = models.TextField(unique=False, null=True)

    cpu_count = models.PositiveIntegerField(unique=False, null=True)

    # Network scan facts
    bios_uuid = models.CharField(max_length=36, unique=False, null=True)
    subscription_manager_id = models.CharField(
        max_length=36, unique=False, null=True)

    cpu_core_per_socket = models.PositiveIntegerField(unique=False, null=True)
    cpu_siblings = models.PositiveIntegerField(unique=False, null=True)
    cpu_hyperthreading = models.NullBooleanField()
    cpu_socket_count = models.PositiveIntegerField(unique=False, null=True)
    cpu_core_count = models.PositiveIntegerField(unique=False, null=True)

    system_creation_date = models.DateField(null=True)

    virtualized_type = models.CharField(max_length=64, unique=False, null=True)
    virtualized_num_guests = models.PositiveIntegerField(
        unique=False, null=True)
    virtualized_num_running_guests = models.PositiveIntegerField(
        unique=False, null=True)

    # VCenter scan facts
    vm_state = models.CharField(max_length=24, unique=False, null=True)
    vm_uuid = models.CharField(max_length=36, unique=False, null=True)
    vm_memory_size = models.PositiveIntegerField(unique=False, null=True)
    vm_dns_name = models.CharField(max_length=128, unique=False, null=True)
    vm_host = models.CharField(max_length=128, unique=False, null=True)
    vm_host_socket_count = models.PositiveIntegerField(unique=False, null=True)
    vm_host_cpu_cores = models.PositiveIntegerField(unique=False, null=True)
    vm_host_cpu_threads = models.PositiveIntegerField(unique=False, null=True)
    vm_cluster = models.CharField(max_length=128, unique=False, null=True)
    vm_datacenter = models.CharField(max_length=128, unique=False, null=True)

    metadata = models.TextField(unique=False, null=False)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'report:{}, ' \
            'name:{}, '\
            'os_name:{}, '\
            'os_version:{}, '\
            'os_release:{}, '\
            'mac_addresses:{}, '\
            'ip_addresses:{}, '\
            'cpu_count:{}, '\
            'bios_uuid:{}, '\
            'subscription_manager_id:{}, '\
            'cpu_core_per_socket:{}, '\
            'cpu_siblings:{}, '\
            'cpu_hyperthreading:{}, '\
            'cpu_socket_count:{}, '\
            'cpu_core_count:{}, '\
            'system_creation_date:{}, '\
            'infrastructure_type:{}, '\
            'virtualized_is_guest:{}, '\
            'virtualized_type:{}, '\
            'virtualized_num_guests:{}, '\
            'virtualized_num_running_guests:{}, '\
            'vm_state:{}, '\
            'vm_uuid:{}, '\
            'vm_memory_size:{}, '\
            'vm_dns_name:{}, '\
            'vm_host:{}, '\
            'vm_host_cpu_cores:{}, '\
            'vm_host_cpu_threads:{}, '\
            'vm_host_socket_count:{}, '\
            'vm_datacenter:{}, '\
            'vm_cluster:{}, '\
            'metadata:{} '.format(self.id,
                                  self.report_id.id,
                                  self.name,
                                  self.os_name,
                                  self.os_version,
                                  self.os_release,
                                  self.mac_addresses,
                                  self.ip_addresses,
                                  self.cpu_count,
                                  self.bios_uuid,
                                  self.subscription_manager_id,
                                  self.cpu_core_per_socket,
                                  self.cpu_siblings,
                                  self.cpu_hyperthreading,
                                  self.cpu_socket_count,
                                  self.cpu_core_count,
                                  self.system_creation_date,
                                  self.infrastructure_type,
                                  self.virtualized_is_guest,
                                  self.virtualized_type,
                                  self.virtualized_num_guests,
                                  self.virtualized_num_running_guests,
                                  self.vm_state,
                                  self.vm_uuid,
                                  self.vm_memory_size,
                                  self.vm_dns_name,
                                  self.vm_host,
                                  self.vm_host_cpu_cores,
                                  self.vm_host_cpu_threads,
                                  self.vm_host_socket_count,
                                  self.vm_datacenter,
                                  self.vm_cluster,
                                  self.metadata) + '}'


class Product(models.Model):
    """Represents a product."""

    PRESENCE_TYPE = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('potential', 'Potential'),
        ('unknown', 'Unknown')
    )

    fingerprint = models.ForeignKey(SystemFingerprint,
                                    models.CASCADE,
                                    related_name='products')
    name = models.CharField(max_length=256, unique=False, null=False)
    version = models.CharField(max_length=256, unique=False, null=True)
    presence = models.CharField(
        max_length=10, choices=PRESENCE_TYPE, default='unknown')

    metadata = models.TextField(unique=False, null=False)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'fingerprint:{}, ' \
            'name:{}, '\
            'version:{}, '\
            'presence:{}, '\
            'metadata:{} '.format(self.id,
                                  self.fingerprint.id,
                                  self.name,
                                  self.version,
                                  self.presence,
                                  self.metadata) + '}'


class Entitlement(models.Model):
    """Represents a Entitlement."""

    fingerprint = models.ForeignKey(SystemFingerprint,
                                    models.CASCADE,
                                    related_name='entitlements')
    name = models.CharField(max_length=256, unique=False, null=True)
    entitlement_id = models.CharField(max_length=256, unique=False, null=True)

    metadata = models.TextField(unique=False, null=False)

    def __str__(self):
        """Convert to string."""
        return '{' + 'id:{}, '\
            'fingerprint:{}, ' \
            'name:{}, '\
            'entitlement_id:{}, '\
            'metadata:{} '.format(self.id,
                                  self.fingerprint.id,
                                  self.name,
                                  self.entitlement_id,
                                  self.metadata) + '}'
