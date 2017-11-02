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

from rest_framework.serializers import (ModelSerializer,
                                        IntegerField,
                                        CharField,
                                        ChoiceField,
                                        UUIDField,
                                        DateField,
                                        NullBooleanField)
from api.models import SystemFingerprint


class FingerprintSerializer(ModelSerializer):
    """Serializer for the Fingerprint model."""

    os_name = CharField(required=True, max_length=64)
    os_release = CharField(required=True, max_length=128)
    os_version = CharField(required=True, max_length=64)

    connection_host = CharField(required=False, max_length=256)
    connection_port = IntegerField(required=False, min_value=0)
    connection_uuid = UUIDField(required=True)

    cpu_count = IntegerField(required=False, min_value=0)
    cpu_core_per_socket = IntegerField(required=False, min_value=0)
    cpu_siblings = IntegerField(required=False, min_value=0)
    cpu_hyperthreading = NullBooleanField(required=False)
    cpu_socket_count = IntegerField(required=False, min_value=0)
    cpu_core_count = IntegerField(required=False, min_value=0)

    system_creation_date = DateField(required=False)
    infrastructure_type = ChoiceField(
        required=True, choices=SystemFingerprint.INFRASTRUCTURE_TYPE)

    virtualized_is_guest = NullBooleanField(required=True)
    virtualized_type = CharField(required=False, max_length=64)
    virtualized_num_guests = IntegerField(required=False, min_value=0)
    virtualized_num_running_guests = IntegerField(required=False, min_value=0)

    class Meta:
        """Meta class for FingerprintSerializer."""

        model = SystemFingerprint
        fields = '__all__'
