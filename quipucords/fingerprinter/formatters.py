"""Fingerprint formatters."""

import datetime
from contextlib import suppress
from logging import getLogger
from typing import Any

logger = getLogger(__name__)


def format_mac_addresses(mac_addresses):
    """Format mac addresses."""
    if isinstance(mac_addresses, list):
        mac_addresses = list(map(lambda x: x.lower(), mac_addresses))
    return mac_addresses


def is_redhat_from_vm_os(vcenter_os_release):
    """Determine whether a system is rhel or not base on vcenter vm.os fact."""
    if vcenter_os_release != "" and vcenter_os_release is not None:  # noqa: PLC1901
        rhel_os_releases = ["red hat enterprise linux", "rhel"]
        for rhel_release in rhel_os_releases:
            if rhel_release in vcenter_os_release.lower():
                return True
    return False


def gigabytes_to_bytes(gigabytes):
    """Convert gigabytes to bytes."""
    if gigabytes is None:
        return None
    return gigabytes * (1024**3)


def convert_architecture(architecture):
    """Convert architecture name."""
    architecture_map = {"amd64": "x86_64"}
    if not architecture_map.get(architecture):
        return architecture
    return architecture_map.get(architecture)


def str_or_none(value) -> str | None:
    """Normalize value to be a string (or None when "empty")."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return str(value).strip()


def float_or_none(value) -> float | None:
    """Convert value to float."""
    with suppress(ValueError, TypeError):
        return float(value)
    return None


def int_or_none(value) -> int | None:
    """Convert value to int."""
    try:
        return int(value)
    except TypeError:
        return None
    except ValueError:
        ...

    with suppress(ValueError, TypeError):
        return int(float_or_none(value))

    return None


def list_or_none(value: Any) -> list | None:
    """Normalize value as list or return None."""
    if isinstance(value, list):
        return value


def dict_or_none(value: Any) -> dict | None:
    """Normalize value as dict or return None."""
    if isinstance(value, dict):
        return value


def list_of_dicts(value: Any) -> list[dict]:
    """Normalize value as a list of dicts."""
    if isinstance(value, list) and all(
        isinstance(inner_val, dict) for inner_val in value
    ):
        return value
    return []


def date_or_none(value: Any) -> datetime.date | None:
    """Normalize value as date or return None."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return None
