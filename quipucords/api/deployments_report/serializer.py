#
# Copyright (c) 2017-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Serializer for system fingerprint models."""

from api.common.serializer import CustomJSONField, NotEmptySerializer
from api.models import (
    DeploymentsReport,
    DetailsReport,
    Entitlement,
    Product,
    SystemFingerprint)

from rest_framework.serializers import (CharField,
                                        ChoiceField,
                                        DateField,
                                        FloatField,
                                        IntegerField,
                                        JSONField,
                                        NullBooleanField,
                                        PrimaryKeyRelatedField,
                                        UUIDField)


class ProductSerializer(NotEmptySerializer):
    """Serializer for the Product model."""

    version = CustomJSONField(required=False)
    metadata = CustomJSONField(required=True)

    class Meta:
        """Meta class for ProductSerializer."""

        model = Product
        fields = ('name', 'version', 'presence', 'metadata')


class EntitlementSerializer(NotEmptySerializer):
    """Serializer for the Entitlement model."""

    metadata = CustomJSONField(required=True)

    class Meta:
        """Meta class for EntitlementSerializer."""

        model = Entitlement
        fields = ('name', 'entitlement_id', 'metadata')


class SystemFingerprintSerializer(NotEmptySerializer):
    """Serializer for the Fingerprint model."""

    # Common facts
    system_platform_id = UUIDField(format='hex_verbose',
                                   read_only=True)
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
    system_last_checkin_date = DateField(required=False)

    system_role = CharField(required=False, max_length=128)
    system_addons = JSONField(required=False)
    system_service_level_agreement = CharField(required=False, max_length=128)
    system_usage_type = CharField(required=False, max_length=128)

    insights_client_id = CharField(required=False, max_length=128)

    virtualized_type = CharField(required=False, max_length=64)

    # VCenter scan facts
    vm_state = CharField(required=False, max_length=24)
    vm_uuid = CharField(required=False, max_length=36)
    vm_dns_name = CharField(required=False, max_length=256)

    vm_host = CharField(required=False, max_length=128)
    vm_host_socket_count = IntegerField(required=False, min_value=0)
    vm_host_core_count = IntegerField(required=False, min_value=0)

    vm_cluster = CharField(required=False, max_length=128)
    vm_datacenter = CharField(required=False, max_length=128)

    products = ProductSerializer(many=True, allow_null=True, required=False)
    entitlements = EntitlementSerializer(many=True,
                                         allow_null=True,
                                         required=False)

    # Red Hat facts
    is_redhat = NullBooleanField(required=False)
    redhat_certs = CharField(required=False)
    # pylint: disable=invalid-name
    redhat_package_count = IntegerField(
        required=False, min_value=0)

    metadata = CustomJSONField(required=True)
    sources = CustomJSONField(required=True)
    etc_machine_id = CharField(required=False, max_length=48)

    class Meta:
        """Meta class for SystemFingerprintSerializer."""

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


class FingerprintField(PrimaryKeyRelatedField):
    """Representation the system fingerprint."""

    def to_representation(self, value):
        """Create output representation."""
        serializer = SystemFingerprintSerializer(value)
        return serializer.data


class DeploymentReportSerializer(NotEmptySerializer):
    """Serializer for the Fingerprint model."""

    # Scan information
    report_type = CharField(read_only=True)
    report_version = CharField(max_length=64, read_only=True)
    report_platform_id = UUIDField(format='hex_verbose',
                                   read_only=True)
    details_report = PrimaryKeyRelatedField(
        queryset=DetailsReport.objects.all())
    report_id = IntegerField(read_only=True)
    cached_fingerprints = CustomJSONField(read_only=True)
    cached_csv = CharField(read_only=True)
    cached_insights = CharField(read_only=True)

    status = ChoiceField(
        read_only=True, choices=DeploymentsReport.STATUS_CHOICES)
    system_fingerprints = FingerprintField(many=True, read_only=True)

    class Meta:
        """Meta class for DeploymentReportSerializer."""

        model = DeploymentsReport
        fields = '__all__'
