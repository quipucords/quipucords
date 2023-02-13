# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Common entities."""

import json
import uuid
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from logging import getLogger
from typing import Dict, List

from django.conf import settings
from django.db.models import F, Q, Value

from api.common.enumerators import (
    SystemPurposeRole,
    SystemPurposeSla,
    SystemPurposeUsage,
)
from api.models import DeploymentsReport, Product, Source, SystemFingerprint
from compat.db import StringAgg

CANONICAL_FACTS = (
    "fqdn",
    "bios_uuid",
    "insights_id",
    "ip_addresses",
    "mac_addresses",
    "satellite_id",
    "subscription_manager_id",
    ("provider_id", "provider_type"),
)

logger = getLogger(__name__)


@dataclass
class HostEntity:
    """A proxy over SystemFingerprint with some extra steps."""

    _fingerprints: SystemFingerprint
    last_discovered: datetime

    def __getattr__(self, attr):
        """
        Retrieve attribute from HostEntity.

        If an attribute doesn't exist in this class, search for it on associated
        fingerprints.
        """
        with suppress(AttributeError):
            return super().__getattribute__(attr)
        return getattr(self._fingerprints, attr)

    def as_list(self):
        """Return a list containing this instance."""
        # HBI expects some fields to be formatted as an array of objects, which
        # sometimes is not applicable
        # (e.g.: Hosts.facts, SystemProfile.network_interfaces)
        return [self]

    @property
    def number_of_cpus(self):
        """Retrieve number of cpus."""
        return self._fingerprints.cpu_count

    @property
    def cores_per_socket(self):
        """Retrieve number of cores per socket."""
        return self._fingerprints.cpu_core_per_socket or self._host_cores_per_socket()

    def _host_cores_per_socket(self):
        with suppress(TypeError, ZeroDivisionError):
            return (
                self._fingerprints.vm_host_core_count
                / self._fingerprints.vm_host_socket_count
            )

    @property
    def number_of_sockets(self):
        """Retrieve number of sockets."""
        cpu_socket_count = self._fingerprints.cpu_socket_count
        host_socket_count = self._fingerprints.vm_host_socket_count
        return cpu_socket_count or host_socket_count

    @property
    def fqdn(self):
        """Retrieve fqdn."""
        return self._fingerprints.name

    @property
    def infrastructure_type(self):
        """
        Map QPC infrastructure types to rh_subscription types.

        Inventory is pretty permissive on the content for this field, but
        rh_subscriptions expects certain values:
        https://github.com/RedHatInsights/rhsm-subscriptions/blob/adbac748687724a5603d3e2dac747acb6ba13b29/src/main/java/org/candlepin/subscriptions/tally/MetricUsageCollector.java#L319-L324  # noqa: E501

        Having this mapped appropriately is important for internal swatch sockets count
        logic.

        https://github.com/RedHatInsights/rhsm-subscriptions/blob/410b8a2f461588255d86a15b8fad0475e334e417/src/main/java/org/candlepin/subscriptions/tally/facts/FactNormalizer.java#L172-L180
        """
        qpc2insights = {
            SystemFingerprint.BARE_METAL: "physical",
            SystemFingerprint.VIRTUALIZED: "virtual",
        }

        _infra_type = self._fingerprints.infrastructure_type
        return qpc2insights.get(_infra_type, _infra_type)

    @property
    def insights_id(self):
        """Retrieve insights id."""
        return self._fingerprints.insights_client_id

    @property
    def ip_addresses(self):
        """Retrieve ip_addresses."""
        with suppress(TypeError):
            return json.loads(self._fingerprints.ip_addresses)

    @property
    def mac_addresses(self):
        """Retrieve mac_addresses."""
        with suppress(TypeError):
            return json.loads(self._fingerprints.mac_addresses)

    @property
    def provider_id(self):
        """Retrieve provider_id.

        On AWS EC2 vms, this should be the content of /var/lib/cloud/data/instance-id
        (which would be aa new fact). We need to map this for other providers as well.
        """
        return None

    @property
    def provider_type(self):
        """Retrieve provider_type.

        provider_type (cloud_provider here) don't necessarily match what HBI expects
        - https://github.com/quipucords/quipucords/blob/8c89dfa6f3a4577d32b9c4314149d1ffcff38e79/quipucords/scanner/network/processing/cloud_provider.py#L14-L17  # noqa: E501
        - https://github.com/RedHatInsights/insights-host-inventory/blob/813a290f3a1c702312d8e02d1e59ba328c6f8143/swagger/api.spec.yaml#L611-L619  # noqa: E501
        """
        valid_providers = {"alibaba", "aws", "azure", "gcp", "ibm"}
        value = self._fingerprints.cloud_provider
        if value and value.lower() in valid_providers:
            return value
        return None

    @property
    def system_purpose(self):
        """Return system_purpose dictionary."""
        sla = self._fingerprints.system_service_level_agreement
        system_purpose_map = (
            ("role", self._fingerprints.system_role, SystemPurposeRole),
            ("usage", self._fingerprints.system_usage_type, SystemPurposeUsage),
            ("sla", sla, SystemPurposeSla),
        )
        _system_purpose = {}
        for name, attr, enum in system_purpose_map:
            # since inventory expects specific values for each key in system_purpose
            # dict, we need to check their values
            # ref: https://github.com/RedHatInsights/insights-host-inventory/blob/b2c067f/swagger/system_profile.spec.yaml#L526-L547  # noqa: E501
            for enum_item in enum:
                if attr == enum_item.value:
                    _system_purpose[name] = attr
                    break
        return _system_purpose

    @property
    def products(self) -> set:
        """
        Return a set of product names present in db.

        Will only work if associated fingerprint was initialized with the proper
        annotated query.
        """
        try:
            return {p for p in self._fingerprints.product_names.split(",") if p != ""}
        except AttributeError as err:
            raise NotImplementedError(
                "Host wasn't properly initialized to list products"
            ) from err

    @property
    def rh_products_installed(self):
        """Return the installed products on the system.

        This is a LEGACY fact on HBI and should be replaced with
        installed_products in the near future.

        installed_products ref: https://github.com/RedHatInsights/insights-host-inventory/blob/986a8323f6d5d94ad721a9746cd50f383dd2594c/swagger/system_profile.spec.yaml#L374-L377  # noqa: E501
        """

        def is_not_none(obj):
            return obj is not None

        name_to_product = {
            "JBoss EAP": "EAP",
            "JBoss Fuse": "FUSE",
            "JBoss BRMS": "DCSM",
            "JBoss Web Server": "JWS",
        }
        products = [name_to_product.get(product) for product in self.products]
        products = list(filter(is_not_none, products))
        if self._fingerprints.is_redhat:
            products.append("RHEL")
        return products

    def has_canonical_facts(self):
        """Return True if host contains at least one canonical fact."""
        for canonical_fact in CANONICAL_FACTS:
            if isinstance(canonical_fact, tuple):
                # special case for facts that should be present together
                if all(getattr(self, fact, None) for fact in canonical_fact):
                    return True
                continue
            if getattr(self, canonical_fact, None):
                return True
        return False


@dataclass
class ReportEntity:
    """An entity representing a Report."""

    _deployment_report: DeploymentsReport
    hosts: List[HostEntity] = field(repr=False, default_factory=list)
    slice_size_limit: int = field(
        default_factory=lambda: settings.QPC_INSIGHTS_REPORT_SLICE_SIZE
    )

    @property
    def report_uuid(self) -> uuid.UUID:
        """Return unique report uuid."""
        return self._deployment_report.report_platform_id

    @property
    def report_id(self) -> int:
        """Return systemwide report id."""
        return self._deployment_report.report_id

    @property
    def report_version(self):
        """Deployment report version."""
        return self._deployment_report.report_version

    @property
    def last_discovered(self) -> datetime:
        """Last time the hosts in this report were discovered."""
        try:
            return self._deployment_report.last_discovered
        except AttributeError:
            # pylint: disable=no-member
            return self._deployment_report.details_report.scanjob.end_time

    @classmethod
    def from_report_id(cls, report_id, skip_non_canonical=True):
        """Create a Report from a report_id."""
        deployment_report, fingerprints = cls._get_deployment_report(report_id)
        hosts = [HostEntity(f, deployment_report.last_discovered) for f in fingerprints]
        if skip_non_canonical:
            hosts = list(filter(cls._has_canonical_facts, hosts))
        cls._validate_hosts_qty(report_id, hosts)
        return ReportEntity(deployment_report, hosts=hosts)

    @classmethod
    def _get_deployment_report(cls, report_id):
        """
        Get deployment report and all related fingerprints.

        The query uses deployment_report id/pk instead of report_id because they SHOULD
        be the same and pk has the advantage of being an indexed column.
        """
        deployment_report = (
            DeploymentsReport.objects.annotate(
                last_discovered=F("details_report__scanjob__end_time")
            )
            .filter(pk=report_id)
            .get()
        )
        # openshift sources won't make sense in insights reports.
        fingerprints = list(
            SystemFingerprint.objects.filter(deployment_report=deployment_report)
            .exclude(sources__icontains=Source.OPENSHIFT_SOURCE_TYPE)
            .annotate(
                product_names=StringAgg(
                    "products__name",
                    default=Value(""),
                    filter=Q(products__presence=Product.PRESENT),
                )
            )
            .all()
        )
        return deployment_report, fingerprints

    @cached_property
    def slices(self) -> Dict[str, "ReportSlice"]:
        """
        Return a dict of ReportSlices mapped to its slice_id.

        If the report_slices don't exist yet, it'll be generated on the spot.
        """
        return self._initialize_report_slices()

    @classmethod
    def _has_canonical_facts(cls, host: HostEntity):
        if host.has_canonical_facts():
            return True
        logger.warning(
            "Host (fingerprint=%d, name=%s) ignored due to lack of canonical facts.",
            host.id,
            host.name,
        )
        return False

    @staticmethod
    def _validate_hosts_qty(report_id, hosts):
        if len(hosts) == 0:
            raise SystemFingerprint.DoesNotExist(
                f"Report ({report_id=} doesn't have valid hosts."
            )

    def _initialize_report_slices(self):
        number_hosts = len(self.hosts)
        report_slices_dict = {}

        for slice_start in range(0, number_hosts, self.slice_size_limit):
            slice_end = self._calc_slice_end(number_hosts, slice_start)
            report_slice = ReportSlice(
                parent_report=self,
                slice_start=slice_start,
                slice_end=slice_end,
            )
            report_slices_dict[report_slice.slice_id] = report_slice
        return report_slices_dict

    def _calc_slice_end(self, number_hosts, slice_start):
        slice_end = slice_start + self.slice_size_limit
        if slice_end > number_hosts:
            return number_hosts
        return slice_end


@dataclass
class ReportSlice:
    """Subset of hosts from a parent_report."""

    parent_report: ReportEntity
    slice_start: int
    slice_end: int
    slice_id: uuid.UUID = field(default_factory=uuid.uuid4)

    @property
    def hosts(self) -> List[HostEntity]:
        """
        Retrieve hosts from this slice.

        Instead creating copies of a subset of hosts from parent_report this only points
        to parent_report using the indexes.
        """
        return self.parent_report.hosts[self.slice_start : self.slice_end]

    @property
    def number_of_hosts(self):
        """Retrieve the number of hosts."""
        return self.slice_end - self.slice_start
