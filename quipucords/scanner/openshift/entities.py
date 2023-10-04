"""Entities representing data collected from OpenShift."""

from __future__ import annotations

import datetime
import json
import re
from typing import Dict, List

from pydantic import Field, validator

from compat.pydantic import BaseModel, raises


def load_entity(data: dict) -> OCPBaseEntity:
    """Transform data into the appropriate OCP entity."""
    kind = data["kind"]
    return OCPBaseEntity._OCP_ENTITIES[kind](**data)


def _update_model_refs():

    for model in OCPBaseEntity._OCP_ENTITIES.values():
        model.update_forward_refs()


class OCPBaseEntity(BaseModel):
    """Base OCP entity. All OCP entities should inherit from this class."""

    _OCP_ENTITIES = {}
    kind: str = None

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
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
            raise NotImplementedError(
                f"{cls.__name__} MUST implement an attribute '_kind'."
            )
        if not isinstance(kind, str):
            raise RuntimeError("'_kind' attribute should be a str.")
        if kind in cls._OCP_ENTITIES:
            raise RuntimeError(f"Entity with {kind=} already registered.")
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
    cluster_uuid: str = None
    creation_timestamp: datetime.datetime = None
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


class OCPWorkload(OCPBaseEntity):
    """
    Entity representing ocp/k8s "Workloads".

    The idea behind workload is to act as anything that manage and run pods such as
    Deployments, StatefulSets, Jobs, custom resources that manage pods, etc...

    More info here: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.26/#-strong-workloads-apis-strong-
    """  # noqa: 501

    name: str
    namespace: str = None
    labels: Dict[str, str] = Field(default_factory=dict)
    container_images: List[str] = Field(default_factory=list)
    init_container_images: List[str] = Field(default_factory=list)
    _kind = "workload"


class OCPPod(OCPWorkload):
    """Entity representing OpenShift Pods."""

    _kind = "pod"

    @property
    def app_name(self):
        """Return app name."""
        # if not available as a label,
        return self.labels.get("app") or self.name.rsplit("-", 1)[0]

    @classmethod
    def from_api_object(cls, api_object):
        """Init OCPPod from object returned from ocp/k8s api."""

        def _get_container_images(container_list):
            container_list = container_list or []
            return list({c["image"] for c in container_list if c.get("image")})

        return cls(
            name=api_object.metadata.name,
            namespace=api_object.metadata.namespace,
            labels=api_object.metadata.labels,
            container_images=_get_container_images(api_object.spec["containers"]),
            init_container_images=_get_container_images(
                api_object.spec["initContainers"]
            ),
        )


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
    def _convert_cpu_value(cls, value):
        # https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu
        millicore_suffix = re.compile(r"^\d+m$")
        if isinstance(value, str) and millicore_suffix.match(value):
            value = float(value.replace("m", "")) / 1000
        return value

    @validator("memory_in_bytes", pre=True)
    def _convert_memory_bytes(cls, value):
        if isinstance(value, str):
            digits, power_name, ends_with_i = cls._parse_resource_string(value)
            if ends_with_i:
                base = 1024
            else:
                base = 1000
            power = {
                "k": 1,
                "m": -1,
                "K": 1,
                "M": 2,
                "G": 3,
                "T": 4,
                "P": 5,
                "E": 6,
            }[power_name]
            val_in_bytes = digits * base**power
            # SystemFingerprint for "system_memory_bytes" is a PositiveIntegerField,
            # so we round the value.
            return round(val_in_bytes)

        return value

    @staticmethod
    def _parse_resource_string(value) -> tuple[int, str, bool]:
        """
        Parse a resource string like 1500Ki.

        returns: tuple of digits, power_name and ends_with_i
        """
        # https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory
        error_message = "Value '%s' is invalid."
        resources_regex = re.compile(r"^(\d+)([mkKMGTPE])(i?)$")
        match = resources_regex.match(value)
        if not match:
            raise ValueError(error_message % value)
        digits = int(match.group(1))
        power_name = match.group(2)
        ends_with_i = match.group(3)
        if ends_with_i and power_name in ["m", "k"]:
            raise ValueError(error_message % value)
        return digits, power_name, ends_with_i


class ClusterOperator(OCPBaseEntity):
    """OCP Cluster Operator."""

    _kind = "cluster-operator"
    name: str
    version: str = None
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None

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


class LifecycleOperator(ClusterOperator):
    """Operator managed by Operator Lifecycle Manager (OLM)."""

    _kind = "olm-operator"
    display_name: str = None
    package: str = None
    source: str = None
    channel: str = None
    namespace: str = None

    @classmethod
    def from_raw_object(cls, raw_object):
        """Instantiate OLM operator using its equivalent api object."""
        installed_version = raw_object.status.currentCSV
        package, version = installed_version.split(".", 1)
        return LifecycleOperator(
            name=raw_object.metadata.name,
            created_at=raw_object.metadata.creationTimestamp,
            updated_at=raw_object.status.lastUpdated,
            namespace=raw_object.metadata.namespace,
            source=raw_object.spec.source,
            channel=raw_object.spec.channel,
            package=package,
            version=version,
        )

    @property
    def cluster_service_version(self):
        """Return currentCSV metadata."""
        return f"{self.package}.{self.version}"


# update nested model references - this should always be the last thing to run
_update_model_refs()
