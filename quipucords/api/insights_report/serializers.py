# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Insights report serializers."""

import socket
from functools import partial

from django.conf import settings
from rest_framework import fields
from rest_framework.serializers import Serializer, SerializerMethodField

from api.common.common_report import create_filename
from api.common.entities import HostEntity
from api.common.serializer import ForcedListSerializer, NotEmptyMixin
from api.status import get_server_id
from quipucords.environment import server_version

default_kwargs = dict(required=False)

# pylint: disable=abstract-method,fixme
# Serializer has update/create as pseudo-abstract methods we don't need to implement
# disable complaints about 'fixme' until DISCOVERY-130 is done


class FactsSerializer(Serializer):
    """Serializer for HBI facts."""

    source_types = fields.ListField()
    last_discovered = fields.DateTimeField()
    qpc_server_version = fields.CharField(default=server_version)
    qpc_server_id = fields.CharField(default=get_server_id)
    rh_products_installed = fields.ListField(child=fields.CharField())


class FactsetSerializer(Serializer):
    """Serializer for Host facts - it should be formatted as a list."""

    namespace = fields.CharField(default="qpc")
    facts = FactsSerializer(source="*")

    def __init__(self, instance=None, **kwargs):
        """Ininialize factset serializer."""
        if instance is not None and not isinstance(instance, list):
            instance = [instance]
        super().__init__(instance, **kwargs)

    class Meta:
        """Serializer configuration."""

        list_serializer_class = ForcedListSerializer


class SystemProfileSerializer(NotEmptyMixin, Serializer):
    """
    Serializer for HBI system profile.

    System profile facts are a set of curated facts with a well defined schema.

    - https://github.com/RedHatInsights/inventory-schemas/blob/master/schemas/system_profile/v1.yaml  # noqa: E501
    - https://consoledot.pages.redhat.com/docs/dev/services/inventory.html#_system_profile  # noqa: E501
    """

    number_of_cpus = fields.IntegerField(**default_kwargs)
    number_of_sockets = fields.IntegerField(**default_kwargs)
    cores_per_socket = fields.IntegerField(**default_kwargs)
    system_memory_bytes = fields.IntegerField(**default_kwargs)
    infrastructure_type = fields.CharField(max_length=100, **default_kwargs)
    infrastructure_vendor = fields.CharField(
        max_length=100, **default_kwargs
    )  # TODO: Looks like virt_type might answer this, but only for virtualized infra
    # yupana builds operating_system from os_release
    os_release = fields.CharField(max_length=100, **default_kwargs)
    arch = fields.CharField(source="architecture", max_length=50, **default_kwargs)
    cloud_provider = fields.CharField(**default_kwargs)


class YupanaHostSerializer(NotEmptyMixin, Serializer):
    """Serializer to format hosts to yupana/hbi."""

    display_name = fields.CharField(source="name", **default_kwargs)
    bios_uuid = fields.CharField(**default_kwargs)
    fqdn = fields.CharField(
        **default_kwargs
    )  # TODO: not sure on this one, just followed old implementation https://github.com/quipucords/quipucords/blob/da644172fb35ad7128ba20372cf64fbf7ff4f367/quipucords/fingerprinter/task.py#L373  # noqa: E501
    insights_id = fields.CharField(source="insights_client_id", **default_kwargs)
    ip_addresses = fields.ListField(child=fields.CharField(), **default_kwargs)
    mac_addresses = fields.ListField(child=fields.CharField(), **default_kwargs)
    provider_id = fields.CharField(
        **default_kwargs
    )  # TODO: this probably needs to be adapted for each provider type
    provider_type = fields.CharField(**default_kwargs)
    satellite_id = fields.CharField(
        **default_kwargs
    )  # TODO: not sure on this one https://github.com/RedHatInsights/insights-host-inventory/blob/813a290f3a1c702312d8e02d1e59ba328c6f8143/swagger/api.spec.yaml#L901-L907  # noqa: E501
    subscription_manager_id = fields.CharField(**default_kwargs)
    etc_machine_id = fields.CharField(**default_kwargs)
    vm_uuid = fields.CharField(**default_kwargs)
    facts = FactsetSerializer(source="*", many=True)
    system_profile = SystemProfileSerializer(source="*", **default_kwargs)
    tags = SerializerMethodField()

    def get_tags(self, host: HostEntity):
        """Format tags to appear as inventory labels."""
        data_collector = settings.QPC_INSIGHTS_DATA_COLLECTOR_LABEL
        hostname = socket.getfqdn()
        ip_address = socket.gethostbyname(hostname)
        tags = {
            "data-collector": data_collector,
            "last-discovered": host.last_discovered,
            "scanner-hostname": hostname,
            "scanner-id": get_server_id(),
            "scanner-ip-address": ip_address,
            "scanner-version": server_version(),
        }
        # this differ from actual HBI format due to yupana constraints
        # yupana will format this accordingly
        # https://github.com/quipucords/yupana/blob/961b376ff80f835203097c43bbf6239a1bc6afbc/yupana/processor/report_slice_processor.py#L226-L252
        return [
            {"namespace": data_collector, "key": key, "value": value}
            for key, value in tags.items()
        ]

    def to_representation(self, instance):
        """Format HostEntity as dict and validate."""
        data = super().to_representation(instance)
        self._validate_provider(data)
        return data

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


class YupanaReportSliceSerializer(Serializer):
    """Formats data to conform to yupana spec."""

    report_slice_id = fields.UUIDField(source="slice_id")
    hosts = YupanaHostSerializer(many=True)


class YupanaSourceSerializer(Serializer):
    """Format source_metadata for yupana payload."""

    report_platform_id = fields.UUIDField(source="report_uuid")
    report_type = fields.CharField(default="insights")
    report_version = fields.CharField()
    qpc_server_report_id = fields.IntegerField(source="report_id")
    qpc_server_version = fields.CharField(default=server_version)
    qpc_server_id = fields.CharField(default=get_server_id)


class ReportSliceSerializer(Serializer):
    """Format report_slice for yupana payload."""

    number_hosts = fields.IntegerField(source="number_of_hosts")


class YupanaMetadataSerializer(Serializer):
    """Serializer for yupana metadata."""

    report_id = fields.UUIDField(source="report_uuid")
    host_inventory_api_version = fields.CharField(default="1.0")
    source = fields.CharField(default="qpc")
    source_metadata = YupanaSourceSerializer(source="*")
    report_slices = fields.DictField(source="slices", child=ReportSliceSerializer())


class YupanaPayloadSerializer(Serializer):
    """Serializer for yupana payload."""

    metadata = YupanaMetadataSerializer(source="*")
    slices = fields.DictField(child=YupanaReportSliceSerializer())

    def to_representation(self, instance):
        """Format ReportEntity and add filenames for tarball construction."""
        data = super().to_representation(instance)
        fname_fn = partial(
            create_filename, file_ext="json", report_id=instance.report_id
        )
        output_data = {
            fname_fn(slice_id): report_slice
            for slice_id, report_slice in data["slices"].items()
        }
        output_data[fname_fn("metadata")] = data["metadata"]
        return output_data
