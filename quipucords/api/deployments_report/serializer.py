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

from api.common.serializer import CustomJSONField, NotEmptySerializer
from api.models import (
    DeploymentsReport,
    DetailsReport,
    Entitlement,
    Product,
    SystemFingerprint,
)


class ProductSerializer(NotEmptySerializer):
    """Serializer for the Product model."""

    version = CustomJSONField(required=False)
    metadata = CustomJSONField(required=True)

    class Meta:
        """Meta class for ProductSerializer."""

        model = Product
        fields = ("name", "version", "presence", "metadata")


class EntitlementSerializer(NotEmptySerializer):
    """Serializer for the Entitlement model."""

    metadata = CustomJSONField(required=True)

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
    user_login_history = JSONField(**default_args)

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
    # pylint: disable=invalid-name
    redhat_package_count = IntegerField(min_value=0, **default_args)

    metadata = JSONField(required=True)
    sources = JSONField(required=True)
    etc_machine_id = CharField(max_length=48, **default_args)

    class Meta:
        """Meta class for SystemFingerprintSerializer."""

        model = SystemFingerprint
        fields = "__all__"

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


class DeploymentReportSerializer(NotEmptySerializer):
    """Serializer for the Fingerprint model."""

    # Scan information
    report_type = CharField(read_only=True)
    report_version = CharField(max_length=64, read_only=True)
    report_platform_id = UUIDField(format="hex_verbose", read_only=True)
    details_report = PrimaryKeyRelatedField(queryset=DetailsReport.objects.all())
    report_id = IntegerField(read_only=True)
    cached_fingerprints = JSONField(read_only=True)
    cached_masked_fingerprints = JSONField(read_only=True)
    cached_csv = CharField(read_only=True)
    cached_masked_csv = CharField(read_only=True)

    status = ChoiceField(read_only=True, choices=DeploymentsReport.STATUS_CHOICES)
    system_fingerprints = FingerprintField(many=True, read_only=True)

    class Meta:
        """Meta class for DeploymentReportSerializer."""

        model = DeploymentsReport
        fields = "__all__"
