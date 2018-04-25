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

"""Serializer for system fingerprint models."""

from rest_framework.serializers import (PrimaryKeyRelatedField,
                                        IntegerField,
                                        CharField,
                                        ChoiceField,
                                        FloatField,
                                        NullBooleanField,
                                        DateField,
                                        ModelSerializer)
from api.models import (SystemFingerprint,
                        FactCollection,
                        Product,
                        Entitlement)
from api.common.serializer import CustomJSONField


class ProductSerializer(ModelSerializer):
    """Serializer for the Product model."""

    version = CustomJSONField(required=False)
    metadata = CustomJSONField(required=True)

    class Meta:
        """Meta class for ProductSerializer."""

        model = Product
        fields = ('name', 'version', 'presence', 'metadata')


class EntitlementSerializer(ModelSerializer):
    """Serializer for the Entitlement model."""

    metadata = CustomJSONField(required=True)

    class Meta:
        """Meta class for EntitlementSerializer."""

        model = Entitlement
        fields = ('name', 'entitlement_id', 'metadata')


class FingerprintSerializer(ModelSerializer):
    """Serializer for the Fingerprint model."""

    # Scan information
    report_id = PrimaryKeyRelatedField(
        queryset=FactCollection.objects.all())

    # Common facts
    name = CharField(required=False, max_length=256)

    os_name = CharField(required=False, max_length=64)
    os_release = CharField(required=False, max_length=128)
    os_version = CharField(required=False, max_length=64)

    infrastructure_type = ChoiceField(
        required=False, choices=SystemFingerprint.INFRASTRUCTURE_TYPE)

    mac_addresses = CustomJSONField(required=False)
    ip_addresses = CustomJSONField(required=False)

    cpu_count = IntegerField(required=False, min_value=0)

    architecture = CharField(required=False, max_length=64)

    # Network scan facts
    bios_uuid = CharField(required=False, max_length=36)
    subscription_manager_id = CharField(required=False, max_length=36)

    cpu_socket_count = IntegerField(required=False, min_value=0)
    cpu_core_count = FloatField(required=False, min_value=0)

    system_creation_date = DateField(required=False)

    virtualized_type = CharField(required=False, max_length=64)

    # VCenter scan facts
    vm_state = CharField(required=False, max_length=24)
    vm_uuid = CharField(required=False, max_length=36)
    vm_dns_name = CharField(required=False, max_length=128)

    vm_host = CharField(required=False, max_length=128)
    vm_host_socket_count = IntegerField(required=False, min_value=0)

    vm_cluster = CharField(required=False, max_length=128)
    vm_datacenter = CharField(required=False, max_length=128)

    products = ProductSerializer(many=True, allow_null=True, required=False)
    entitlements = EntitlementSerializer(many=True,
                                         allow_null=True,
                                         required=False)

    # Red Hat facts
    is_redhat = NullBooleanField(required=False)
    redhat_certs = CharField(required=False, max_length=128)
    # pylint: disable=invalid-name
    redhat_package_count = IntegerField(
        required=False, min_value=0)

    metadata = CustomJSONField(required=True)
    sources = CustomJSONField(required=True)

    class Meta:
        """Meta class for FingerprintSerializer."""

        model = SystemFingerprint
        fields = '__all__'

    def create(self, validated_data):
        """Create a system fingerprint."""
        products_data = validated_data.pop('products', [])
        entitlements_data = validated_data.pop('entitlements', [])
        fingerprint = SystemFingerprint.objects.create(**validated_data)
        for product_data in products_data:
            Product.objects.create(fingerprint=fingerprint,
                                   **product_data)
        for entitlement_data in entitlements_data:
            Entitlement.objects.create(fingerprint=fingerprint,
                                       **entitlement_data)
        return fingerprint
