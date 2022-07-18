# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Common entities."""

import uuid
from dataclasses import dataclass, field
from functools import cached_property
from typing import Dict, List

from django.conf import settings

from api.models import DeploymentsReport, SystemFingerprint


@dataclass
class ReportEntity:
    """An entity representing a Report."""

    _deployment_report: DeploymentsReport
    hosts: List[SystemFingerprint] = field(repr=False)
    slice_size_limit: int = settings.QPC_INSIGHTS_REPORT_SLICE_SIZE

    @property
    def report_uuid(self) -> uuid.UUID:
        """Return unique report uuid."""
        return self._deployment_report.report_platform_id

    @property
    def report_id(self) -> int:
        """Return systemwide report id."""
        return self._deployment_report.report_id

    @classmethod
    def from_report_id(cls, report_id):
        """Create a Report from a report_id."""
        deployment_report, hosts = cls._get_deployment_report(report_id)
        return ReportEntity(deployment_report, hosts=hosts)

    @classmethod
    def _get_deployment_report(cls, report_id):
        """Get deployment report and all related fingerprints.

        The query uses deployment_report id/pk instead of report_id because they SHOULD
        be the same and pk has the advantage of being an indexed column.
        """
        fingerprints = list(
            SystemFingerprint.objects.select_related("deployment_report")
            .filter(deployment_report_id=report_id)
            .all()
        )
        try:
            return fingerprints[0].deployment_report, fingerprints
        except IndexError as error:
            # querying from fingerprint to deployment report has the benefit of
            # generating a single query - but it has the downside of the following
            # ambiguity (which one doesn't exist?)
            raise SystemFingerprint.DoesNotExist(
                f"Report with '{report_id=}' either doesn't exist or don't have hosts."
            ) from error

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
    def hosts(self) -> List[SystemFingerprint]:
        """
        Retrieve hosts from this slice.

        Instead creating copies of a subset of hosts from parent_report this only points
        to parent_report using the indexes.
        """
        return self.parent_report.hosts[self.slice_start : self.slice_end]
