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
from dataclasses import asdict, dataclass, field
from typing import Dict, List


class ToDictMixin:
    """Mixin that adds "to_dict" method to dataclasses."""

    def to_dict(self):
        """Convert object to dict."""
        return asdict(self)


class OCPBaseEntity(ToDictMixin):
    """Base OCP entity. All OCP entities should inherit from this class."""

    OCP_ENTITIES = {}

    def __post_init__(self):
        """Run after dataclass '__init__'."""
        # avoid kind being improperly set
        self.kind = self.__class__.kind  # noqa: E1101

    def __new__(cls, *args, **kwargs):
        """Override __new__ magic method."""
        if cls == OCPBaseEntity:
            raise TypeError(f"{cls.__name__} can't be initialized.")
        return super().__new__(cls)

    def __init_subclass__(cls, **kwargs):
        """
        Override __init_subclass__ magic method.

        Setup subclasses enforcing some standards.
        """
        super().__init_subclass__(**kwargs)
        kind = cls._get_kind()
        cls._set_kind_as_annotation(kind)
        cls.OCP_ENTITIES[kind] = cls

    @classmethod
    def _get_kind(cls):
        try:
            kind = cls.kind
        except AttributeError:
            raise NotImplementedError(  # pylint: disable=raise-missing-from
                f"{cls.__name__} MUST implement an attribute 'kind'."
            )
        assert isinstance(kind, str), "'kind' attribute should be an str."
        assert kind not in cls.OCP_ENTITIES, f"Entity with {kind=} already registered."
        return kind

    @classmethod
    def _set_kind_as_annotation(cls, kind):
        try:
            # force kind to work as a dataclass field.
            cls.__annotations__["kind"] = field(default=kind)
        except AttributeError:
            raise AttributeError(  # pylint: disable=raise-missing-from
                f"{cls.__name__} don't have type annotations. "
                "Did you forgot to implement it's dataclass fields?"
            )


@dataclass
class OCPProject(OCPBaseEntity):
    """Entity representing OpenShift Projects/Namespaces."""

    name: str
    labels: Dict[str, str]
    deployments: List["OCPDeployment"] = field(default_factory=list)
    errors: Dict[str, "OCPError"] = field(default_factory=dict)
    kind = "namespace"


@dataclass
class OCPDeployment(OCPBaseEntity):
    """Entity representing OpenShift Deployments."""

    name: str
    labels: Dict[str, str]
    container_images: List[str]
    init_container_images: List[str]
    kind = "deployment"


@dataclass
class OCPError(Exception, OCPBaseEntity):
    """Entity/Error class for OpenShift errors."""

    status: int = None
    reason: str = None
    message: str = None
    kind = "error"

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

    def __str__(self):
        """Format as string."""
        return str(self.to_dict())
