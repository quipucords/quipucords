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

"""Serializer for system fingerprint models."""

from rest_framework.serializers import (IntegerField,
                                        CharField,
                                        ChoiceField,
                                        DateField,
                                        NullBooleanField,
                                        ModelSerializer)
from api.models import SystemFingerprint


class FingerprintSerializer(ModelSerializer):
    """Serializer for the Fingerprint model."""

    os_name = CharField(required=True, max_length=64)
    os_release = CharField(required=True, max_length=128)
    os_version = CharField(required=False, max_length=64)

    bios_uuid = CharField(required=False, max_length=36)
    subscription_manager_id = CharField(required=False, max_length=36)

    cpu_count = IntegerField(required=False, min_value=0)
    cpu_core_per_socket = IntegerField(required=False, min_value=0)
    cpu_hyperthreading = NullBooleanField(required=False)
    cpu_socket_count = IntegerField(required=False, min_value=0)
    cpu_core_count = IntegerField(required=False, min_value=0)

    system_creation_date = DateField(required=False)
    source_type = ChoiceField(
        required=True, choices=SystemFingerprint.SOURCE_TYPE)
    infrastructure_type = ChoiceField(
        required=True, choices=SystemFingerprint.INFRASTRUCTURE_TYPE)

    virtualized_is_guest = NullBooleanField(required=True)
    virtualized_type = CharField(required=False, max_length=64)
    virtualized_num_guests = IntegerField(required=False, min_value=0)
    virtualized_num_running_guests = IntegerField(required=False, min_value=0)

    virtualized_host = CharField(required=False, max_length=128)
    virtualized_host_socket_count = IntegerField(required=False, min_value=0)
    virtualized_cluster = CharField(required=False, max_length=128)
    virtualized_datacenter = CharField(required=False, max_length=128)

    class Meta:
        """Meta class for FingerprintSerializer."""

        model = SystemFingerprint
        fields = ['id', 'fact_collection_id', 'source_id', 'source_type',
                  'os_name', 'os_version', 'os_release',
                  'bios_uuid', 'subscription_manager_id',
                  'cpu_count', 'cpu_socket_count', 'cpu_core_count',
                  'cpu_hyperthreading', 'cpu_core_per_socket',
                  'system_creation_date',
                  'infrastructure_type',
                  'virtualized_is_guest', 'virtualized_type',
                  'virtualized_num_guests', 'virtualized_num_running_guests',
                  'virtualized_host', 'virtualized_host_socket_count',
                  'virtualized_cluster', 'virtualized_datacenter']
