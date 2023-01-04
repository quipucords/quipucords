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
import re
from datetime import datetime
from typing import Dict, List

from kubernetes.dynamic.resource import ResourceInstance as K8SResourceInstance
from openshift.dynamic.resource import ResourceInstance as OCPResourceInstance
from pydantic import Field, validator  # pylint: disable=no-name-in-module

from compat.pydantic import BaseModel, raises

MEMORY_CONVERSION_ERROR = "This value couldn't be converted."


def load_entity(data: dict) -> OCPBaseEntity:
    """Trasform data into the appropriate OCP entity."""
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


class OCPNode(OCPBaseEntity):
    """Entity representing OpenShift Node."""

    name: str
    creation_timestamp: datetime = None
    labels: Dict[str, str] = None
    addresses: List[dict] = None
    allocatable: NodeResources = None
    capacity: NodeResources = None
    architecture: str = None
    kernel_version: str = None
    machine_id: str = None
    operating_system: str = None
    taints: List[dict] = None
    errors: Dict[str, OCPError] = Field(default_factory=dict)
    _kind = "node"


class OCPProject(OCPBaseEntity):
    """Entity representing OpenShift Projects/Namespaces."""

    name: str
    cluster_uuid: str = None
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


class NodeResources(OCPBaseEntity):
    """Class representing node's resources."""

    cpu: float = None
    memory_in_bytes: int = None
    pods: int = None
    _kind = "node-resources"

    @validator("cpu", pre=True)
    def _convert_cpu_value(cls, value):  # pylint: disable=no-self-argument
        # https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu
        millicore_suffix = re.compile(r"^\d+m$")
        if isinstance(value, str) and millicore_suffix.match(value):
            value = float(value.replace("m", "")) / 1000
        return value

    @validator("memory_in_bytes", pre=True)
    def _convert_memory_bytes(cls, value):  # pylint: disable=no-self-argument
        # https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory
        if isinstance(value, str):
            resources_regex = re.compile(r"^(\d+)([KMGTPE])(i?)$")
            match = resources_regex.match(value)
            if not match:
                raise ValueError(MEMORY_CONVERSION_ERROR)
            value = int(match.group(1))
            power_name = match.group(2)
            ends_with_i = match.group(3)
            if ends_with_i:
                base = 1024
            else:
                base = 1000
            power = {
                "K": 1,
                "M": 2,
                "G": 3,
                "T": 4,
                "P": 5,
                "E": 6,
            }[power_name]
            return value * base**power

        return value


class ClusterOperator(BaseModel):
    """OCP Cluster Operator."""

    _kind = "cluster-operator"
    name: str
    version: str = None
    created_at: datetime = None
    updated_at: datetime = None

    @classmethod
    def from_raw_object(cls, raw_object):
        """Instantiate ClusterOperator using its equivalent api object."""

        def _get_version(raw_object):
            for version in raw_object.status.versions:
                if version.name == "operator":
                    return version.version
            return None

        return ClusterOperator(
            name=raw_object.metadata.name,
            created_at=raw_object.metadata.creationTimestamp,
            updated_at=raw_object.status.conditions[0].lastTransitionTime,
            version=_get_version(raw_object),
        )


class OLMOperator(ClusterOperator):
    """Operator managed by Operator Lifecycle Manager."""

    _kind = "olm-operator"
    package: str = None
    source: str = None
    channel: str = None
    namespace: str = None

    @classmethod
    def from_raw_object(cls, raw_object):
        installed_version = raw_object.status.installedCSV
        package, version = installed_version.split(".", 1)
        return OLMOperator(
            name=raw_object.metadata.name,
            created_at=raw_object.metadata.creationTimestamp,
            updated_at=raw_object.status.lastUpdated,
            namespace=raw_object.metadata.namespace,
            source=raw_object.spec.source,
            channel=raw_object.spec.channel,
            package=package,
            version=version,
        )


class OCPOperators(OCPBaseEntity):
    """OCP Operators."""

    _kind = "operators"
    cluster_operators: List[ClusterOperator] = Field(default_factory=list)
    olm_operators: List[OLMOperator] = Field(default_factory=list)
    errors: Dict[str, OCPError] = Field(default_factory=dict)

    @validator("cluster_operators", pre=True)
    def _init_cluster_operators(cls, values):
        return cls._parse_resource_instance(values, ClusterOperator.from_raw_object)

    @validator("olm_operators", pre=True)
    def _init_olm_operators(cls, values):
        return cls._parse_resource_instance(values, OLMOperator.from_raw_object)

    @classmethod
    def _parse_resource_instance(cls, values, parser):

        if isinstance(values, (K8SResourceInstance, OCPResourceInstance)):
            return [parser(res) for res in values.items]
        return values


# update nested model references - this should always be the last thing to run
_update_model_refs()
