# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Insights report serializers."""

from rest_framework import fields
from rest_framework.serializers import Serializer, ValidationError

from api.insights_report.constants import CANONICAL_FACTS

default_kwargs = dict(required=False)

# pylint: disable=abstract-method,fixme
# Serializer has update/create as pseudo-abstract methods we don't need to implement
# disable complaints about 'fixme' until DISCOVERY-130 is done


class SystemProfileSerializer(NotEmptyMixin, Serializer):
    """
    Serializer for HBI system profile.

    System profile facts are a set of curated facts with a well defined schema.

    - https://github.com/RedHatInsights/inventory-schemas/blob/master/schemas/system_profile/v1.yaml  # noqa: E501
    - https://consoledot.pages.redhat.com/docs/dev/services/inventory.html#_system_profile  # noqa: E501
    """

    number_of_cpus = fields.IntegerField(source="cpu_count", **default_kwargs)
    system_memory_bytes = fields.IntegerField(
        **default_kwargs
    )  # TODO: not mapped yet to a fingerprint
    infrastructure_type = fields.CharField(max_length=100, **default_kwargs)
    infrastructure_vendor = fields.CharField(
        max_length=100, **default_kwargs
    )  # TODO: Looks like virt_type might answer this, but only for virtualized infra
    # yupana builds operating_system from os_release
    os_release = fields.CharField(max_length=100, **default_kwargs)
    arch = fields.CharField(source="architecture", max_length=50, **default_kwargs)


class YupanaHostSerializer(NotEmptyMixin, Serializer):
    """Serializer to format hosts to yupana/hbi."""

    display_name = fields.CharField(source="name", **default_kwargs)
    bios_uuid = fields.CharField(**default_kwargs)
    fqdn = fields.CharField(
        source="name", **default_kwargs
    )  # TODO: not sure on this one, just followed old implementation https://github.com/quipucords/quipucords/blob/da644172fb35ad7128ba20372cf64fbf7ff4f367/quipucords/fingerprinter/task.py#L373  # noqa: E501
    insights_id = fields.CharField(source="insights_client_id", **default_kwargs)
    ip_addresses = fields.ListField(child=fields.CharField(), **default_kwargs)
    mac_addresses = fields.ListField(child=fields.CharField(), **default_kwargs)
    provider_id = fields.CharField(
        source="name", **default_kwargs
    )  # TODO: not sure on this one
    provider_type = fields.CharField(**default_kwargs)
    satellite_id = fields.CharField(
        **default_kwargs
    )  # TODO: not sure on this one https://github.com/RedHatInsights/insights-host-inventory/blob/813a290f3a1c702312d8e02d1e59ba328c6f8143/swagger/api.spec.yaml#L901-L907  # noqa: E501
    subscription_manager_id = fields.CharField(**default_kwargs)
    system_profile = SystemProfileSerializer(source="*", **default_kwargs)

    def to_representation(self, instance):
        """Format HostEntity as dict and validate."""
        data = super().to_representation(instance)
        self.validate(data)
        return data

    def validate(self, attrs: dict):
        """Validate serializer data."""
        attrs = self._validate_canonical_facts(attrs)
        attrs = self._validate_provider(attrs)
        return attrs

    def _validate_provider(self, attrs: dict):
        # hbi requires either provider_id and provider_type or none
        # https://github.com/RedHatInsights/insights-host-inventory/blob/813a290f3a1c702312d8e02d1e59ba328c6f8143/swagger/api.spec.yaml#L943-L957  # noqa: E501
        provider_attrs = {"provider_id", "provider_type"}
        present_provider_attr_set = provider_attrs & set(attrs)
        if len(present_provider_attr_set) != 1:
            return attrs

        present_provider_attr = present_provider_attr_set.pop()
        attrs.pop(present_provider_attr)
        return attrs

    def _validate_canonical_facts(self, attrs):
        if not set(attrs).intersection(CANONICAL_FACTS):
            raise ValidationError(
                "At least one 'canonical fact' must be present on the report. "
                f"(Canonical facts are: {CANONICAL_FACTS})"
            )
        return attrs


class YupanaReportSliceSerializer(Serializer):
    """Formats data to conform to yupana spec."""

    report_slice_id = fields.UUIDField(source="slice_id")
    hosts = YupanaHostSerializer(many=True)
