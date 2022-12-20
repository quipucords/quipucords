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
from typing import Dict, List

from pydantic import Field  # pylint: disable=no-name-in-module

from compat.pydantic import BaseModel, raises


class OCPBaseEntity(BaseModel):
    """Base OCP entity. All OCP entities should inherit from this class."""


class OCPProject(OCPBaseEntity):
    """Entity representing OpenShift Projects/Namespaces."""

    name: str
    labels: Dict[str, str]
    deployments: List["OCPDeployment"] = Field(default_factory=list)
    errors: Dict[str, "OCPError"] = Field(default_factory=dict)


class OCPDeployment(OCPBaseEntity):
    """Entity representing OpenShift Deployments."""

    name: str
    labels: Dict[str, str]
    container_images: List[str]
    init_container_images: List[str]


@raises(ValueError)
class OCPError(OCPBaseEntity):
    """Entity/Error class for OpenShift errors."""

    status: int = None
    reason: str = None
    message: str = None

    @classmethod
    def from_api_exception(cls, api_exception):
        """Initialize OCPError from kubernetes ApiException."""
        error_message = cls._parse_error_message(api_exception.body)
        # we need explicitly return OCPError instead of cls because the latter
        # is not modified by the decorator.
        return OCPError(
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

    def __str__(self):
        """Format as string."""
        return str(self.dict())

    def __raise__(self):
        return (self.message,)
