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
