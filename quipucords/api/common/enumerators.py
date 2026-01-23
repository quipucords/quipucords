"""Common enumerators."""

from enum import Enum


class SystemPurposeRole(Enum):
    """Representing system purpose role values accepted in HBI system profile."""

    WORKSTATION = "Red Hat Enterprise Linux Workstation"
    SERVER = "Red Hat Enterprise Linux Server"
    NODE = "Red Hat Enterprise Linux Compute Node"


class SystemPurposeSla(Enum):
    """Representing system purpose SLA values accepted in HBI system profile."""

    PREMIUM = "Premium"
    SELF_SUPORT = "Self-Support"
    STANDARD = "Standard"


class SystemPurposeUsage(Enum):
    """Representing system purpose usage values accepted in HBI system profile."""

    DEVELOPMENT_TEST = "Development/Test"
    PRODUCTION = "Production"
    DISASTER_RECOVERY = "Disaster Recovery"


class LightspeedCannotPublishReason(Enum):
    """Reason why report can't be published to Lightspeed."""

    NO_CONNECTION = "no_connection"
    NO_CREDENTIALS = "no_credentials"
    AUTH_FAILED = "auth_failed"
    # TOKEN_EXPIRED = "token_expired"  # TODO: TBD if we check token periodically
    NOT_COMPLETE = "not_complete"
    NO_HOSTS = "no_hosts"
