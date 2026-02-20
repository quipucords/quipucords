"""Serializer for system fingerprint models."""

from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    FloatField,
    IntegerField,
    JSONField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    UUIDField,
)

from api.common.common_report import REPORT_TYPE_DEPLOYMENT
from api.common.serializer import NotEmptySerializer
from api.models import (
    DeploymentsReport,
    Entitlement,
    Product,
    SystemFingerprint,
)


class ProductSerializer(NotEmptySerializer):
    """Serializer for the Product model."""

    version = JSONField(required=False)
    metadata = JSONField(required=True)

    class Meta:
        """Meta class for ProductSerializer."""

        model = Product
        fields = ("name", "version", "presence", "metadata")


class EntitlementSerializer(NotEmptySerializer):
    """Serializer for the Entitlement model."""

    metadata = JSONField(required=True)

    class Meta:
        """Meta class for EntitlementSerializer."""

        model = Entitlement
        fields = ("name", "entitlement_id", "metadata")


default_args = {"required": False, "allow_null": True}


class SystemFingerprintSerializer(ModelSerializer):
    """Serializer for the Fingerprint model."""

    # Common facts
    name = CharField(max_length=256, **default_args)

    os_name = CharField(max_length=64, **default_args)
    os_release = CharField(max_length=128, **default_args)
    os_version = CharField(max_length=64, **default_args)

    infrastructure_type = ChoiceField(
        required=False, choices=SystemFingerprint.INFRASTRUCTURE_TYPE
    )

    cloud_provider = CharField(max_length=16, **default_args)

    mac_addresses = JSONField(**default_args)
    ip_addresses = JSONField(**default_args)

    cpu_count = IntegerField(min_value=0, **default_args)

    architecture = CharField(max_length=64, **default_args)

    # Network scan facts
    bios_uuid = CharField(max_length=36, **default_args)
    subscription_manager_id = CharField(max_length=36, **default_args)

    cpu_socket_count = IntegerField(min_value=0, **default_args)
    cpu_core_count = FloatField(min_value=0, **default_args)
    cpu_core_per_socket = IntegerField(min_value=0, **default_args)
    cpu_hyperthreading = BooleanField(**default_args)

    installed_products = JSONField(**default_args)

    system_creation_date = DateField(**default_args)
    system_last_checkin_date = DateField(**default_args)

    system_purpose = JSONField(**default_args)
    system_role = CharField(max_length=128, **default_args)
    system_addons = JSONField(**default_args)
    system_service_level_agreement = CharField(max_length=128, **default_args)
    system_usage_type = CharField(max_length=128, **default_args)

    insights_client_id = CharField(max_length=128, **default_args)

    virtualized_type = CharField(max_length=64, **default_args)
    system_user_count = IntegerField(min_value=0, **default_args)

    # VCenter scan facts
    vm_state = CharField(max_length=24, **default_args)
    vm_uuid = CharField(max_length=36, **default_args)
    vm_dns_name = CharField(max_length=256, **default_args)

    virtual_host_name = CharField(max_length=128, **default_args)
    virtual_host_uuid = CharField(max_length=36, **default_args)
    vm_host_socket_count = IntegerField(min_value=0, **default_args)
    vm_host_core_count = IntegerField(min_value=0, **default_args)

    vm_cluster = CharField(max_length=128, **default_args)
    vm_datacenter = CharField(max_length=128, **default_args)

    products = ProductSerializer(many=True, **default_args)
    entitlements = EntitlementSerializer(many=True, **default_args)

    # Red Hat facts
    is_redhat = BooleanField(**default_args)
    redhat_certs = CharField(**default_args)
    redhat_package_count = IntegerField(min_value=0, **default_args)

    metadata = JSONField(required=True)
    sources = JSONField(required=True)
    etc_machine_id = CharField(max_length=48, **default_args)

    class Meta:
        """Meta class for SystemFingerprintSerializer."""

        model = SystemFingerprint
        exclude = (
            "created_at",
            "updated_at",
        )  # TODO Include these datetime fields in a future API version.

    def create(self, validated_data):
        """Create a system fingerprint."""
        products_data = validated_data.pop("products", [])
        entitlements_data = validated_data.pop("entitlements", [])
        fingerprint = SystemFingerprint.objects.create(**validated_data)
        for product_data in products_data:
            Product.objects.create(fingerprint=fingerprint, **product_data)
        for entitlement_data in entitlements_data:
            Entitlement.objects.create(fingerprint=fingerprint, **entitlement_data)
        return fingerprint


class FingerprintField(PrimaryKeyRelatedField):
    """Representation the system fingerprint."""

    def to_representation(self, value):
        """Create output representation."""
        serializer = SystemFingerprintSerializer(value)
        return serializer.data


class DeploymentReportSerializer(ModelSerializer):
    """Serializer for the DeploymentReport."""

    report_id = IntegerField(read_only=True)
    status = CharField(max_length=16)
    report_type = CharField(read_only=True, default=REPORT_TYPE_DEPLOYMENT)
    report_version = CharField(max_length=64, read_only=True)
    report_platform_id = UUIDField(format="hex_verbose", read_only=True)
    system_fingerprints = SystemFingerprintSerializer(read_only=True)

    class Meta:
        """Metaclass for DeploymentReportSerializer."""

        model = DeploymentsReport
        fields = (
            "report_id",
            "status",
            "report_type",
            "report_version",
            "report_platform_id",
            "system_fingerprints",
        )
