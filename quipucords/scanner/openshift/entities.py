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

from __future__ import annotations

import json
from typing import Dict, List

from pydantic import Field  # pylint: disable=no-name-in-module

from compat.pydantic import BaseModel, raises


def load_entity(data: dict) -> OCPBaseEntity:
    """Transform data into the appropriate OCP entity."""
    # pylint: disable=protected-access
    kind = data["kind"]
    return OCPBaseEntity._OCP_ENTITIES[kind](**data)


def _update_model_refs():
    # pylint: disable=protected-access
    for model in OCPBaseEntity._OCP_ENTITIES.values():
        model.update_forward_refs()


class OCPBaseEntity(BaseModel):
    """Base OCP entity. All OCP entities should inherit from this class."""

    _OCP_ENTITIES = {}
    kind: str = None

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super().__init__(*args, **kwargs)
        # force kind value
        self.kind = self._kind

    def __init_subclass__(cls, **kwargs):
        """
        Override __init_subclass__ magic method.

        Setup subclasses enforcing some standards.
        """
        super().__init_subclass__(**kwargs)
        kind = cls._get_kind()
        cls._OCP_ENTITIES[kind] = cls

    @classmethod
    def _get_kind(cls):
        """Get and validate kind."""
        try:
            kind = cls._kind
        except AttributeError:
            raise NotImplementedError(  # pylint: disable=raise-missing-from
                f"{cls.__name__} MUST implement an attribute '_kind'."
            )
        assert isinstance(kind, str), "'_kind' attribute should be a str."
        assert kind not in cls._OCP_ENTITIES, f"Entity with {kind=} already registered."
        return kind


class OCPCluster(OCPBaseEntity):
    """Entity representing OpenShift Cluster."""

    uuid: str
    version: str = None
    errors: Dict[str, OCPError] = Field(default_factory=dict)
    _kind = "cluster"

    @property
    def name(self):
        """Cluster 'name'."""
        return f"cluster:{self.uuid}"


class OCPProject(OCPBaseEntity):
    """Entity representing OpenShift Projects/Namespaces."""

    name: str
    labels: Dict[str, str]
    deployments: List[OCPDeployment] = Field(default_factory=list)
    errors: Dict[str, OCPError] = Field(default_factory=dict)
    _kind = "namespace"


class OCPDeployment(OCPBaseEntity):
    """Entity representing OpenShift Deployments."""

    name: str
    labels: Dict[str, str]
    container_images: List[str]
    init_container_images: List[str]
    _kind = "deployment"


@raises(ValueError)
class OCPError(OCPBaseEntity):
    """Entity/Error class for OpenShift errors."""

    status: int = None
    reason: str = None
    message: str = None
    _kind = "error"

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
        """Arguments for raised exception."""
        return (self.message,)


# update nested model references - this should always be the last thing to run
_update_model_refs()
