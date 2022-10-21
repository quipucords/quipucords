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
from typing import Dict, List

from django.conf import settings
from django.db.models import F

from api.models import DeploymentsReport, Source, SystemFingerprint


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
    def from_report_id(cls, report_id):
        """Create a Report from a report_id."""
        deployment_report, fingerprints = cls._get_deployment_report(report_id)
        hosts = [HostEntity(f, deployment_report.last_discovered) for f in fingerprints]
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
            .all()
        )
        if len(fingerprints) == 0:
            raise SystemFingerprint.DoesNotExist(
                f"Report with '{report_id=}' don't have hosts."
            )
        return deployment_report, fingerprints

    @cached_property
    def slices(self) -> Dict[str, "ReportSlice"]:
        """
        Return a dict of ReportSlices mapped to its slice_id.

        If the report_slices don't exist yet, it'll be generated on the spot.
        """
        return self._initialize_report_slices()

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
