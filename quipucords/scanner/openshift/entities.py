# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Entities representing data collected from OpenShift."""
import json
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class OCPProject:
    """Entity representing OpenShift Projects/Namespaces."""

    name: str
    labels: Dict[str, str]
    deployments: List["OCPDeployment"] = field(default_factory=list)
    errors: Dict[str, "OCPError"] = field(default_factory=dict)


@dataclass
class OCPDeployment:
    """Entity representing OpenShift Deployments."""

    name: str
    labels: Dict[str, str]
    container_images: List[str]
    init_container_images: List[str]


@dataclass
class OCPError(Exception):
    """Entity/Error class for OpenShift errors."""

    status: int = None
    reason: str = None
    message: str = None

    @classmethod
    def from_api_exception(cls, api_exception):
        """Initialize OCPError from kubernetes ApiException."""
        error_message = cls._parse_error_message(api_exception.body)
        return cls(
            status=api_exception.status,
            reason=api_exception.reason,
            message=error_message,
        )

    @staticmethod
    def _parse_error_message(error):
        try:
            error_data = json.loads(error)
            return error_data["message"]
        except (json.JSONDecodeError, KeyError):
            return error
