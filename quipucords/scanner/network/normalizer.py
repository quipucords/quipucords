"""normalizer for network scans."""

import ipaddress

from constants import DataSources
from fingerprinter import formatters
from scanner.normalizer import (
    FactMapper,
    NormalizedResult,
    SystemProfileNormalizer,
    str_or_none,
)


def infrastructure_type_normalizer(
    *, virt_what_type=None, virt_type=None, subman_virt_is_guest=None
):
    """Normalize infrastructure type."""
    if virt_what_type == "bare metal":
        return NormalizedResult("physical", raw_fact_keys=["virt_what_type"])
    elif virt_type:
        return NormalizedResult("virtualized", raw_fact_keys=["virt_type"])
    elif subman_virt_is_guest:
        # We don't know virt_type, but subscription-manager says it's a guest.
        # So, we assume it's virtualized. See also: DISCOVERY-243.
        return NormalizedResult("virtualized", raw_fact_keys=["subman_virt_is_guest"])
    return NormalizedResult(None, raw_fact_keys=None)


def ip_address_normalizer(ifconfig_ip_addresses: list[str]):
    """Normalize ip_address."""
    # https://github.com/quipucords/quipucords/blob/e65d0e3deb23adca41ceed701e4d002187e593f6/quipucords/api/common/entities.py#L124-L136
    if ifconfig_ip_addresses is None:
        return []
    addresses = []
    for raw_ip in ifconfig_ip_addresses:
        ip_addr = ipaddress.ip_address(raw_ip)
        # raw fact is only collecting ipv4 addresses
        if isinstance(ip_addr, ipaddress.IPv4Address):
            addresses.append(str(ip_addr))
    return addresses


def network_interfaces(ip_addresses: list[str]):
    """Normalize network interfaces."""
    interface = {
        "name": "unknown",  # required by yuptoo
        "ipv4_addresses": ip_addresses or [],
        "ipv6_addresses": [],  # required by yuptoo
    }
    return [interface]


class Normalizer(SystemProfileNormalizer):
    """Network Scan normalizer."""

    source_type = DataSources.NETWORK.value

    mac_addresses = FactMapper(
        "ifconfig_mac_addresses", formatters.format_mac_addresses
    )
    ip_addresses = FactMapper("ifconfig_ip_addresses", ip_address_normalizer)
    bios_uuid = FactMapper("dmi_system_uuid", str_or_none)
    insights_id = FactMapper("insights_client_id", str_or_none)
    subscription_manager_id = FactMapper("subscription_manager_id", str_or_none)
    number_of_cpus = FactMapper("cpu_core_count", int)
    number_of_sockets = FactMapper("cpu_socket_count", int)
    cores_per_socket = FactMapper("cpu_core_per_socket", int)
    system_memory_bytes = FactMapper("system_memory_bytes", int)
    infrastructure_type = FactMapper(
        ["virt_what_type", "virt_type", "subman_virt_is_guest"],
        infrastructure_type_normalizer,
    )
    infrastructure_vendor = FactMapper("virt_type", str_or_none)
    os_release = FactMapper("etc_release_release", str_or_none)
    arch = FactMapper("uname_processor", str_or_none)
    cloud_provider = FactMapper("cloud_provider", str_or_none)
    system_purpose = FactMapper("system_purpose_json", dict)
    network_interfaces = FactMapper(
        None, network_interfaces, dependencies=["ip_addresses"]
    )
    # ----- non canonical/system profile facts ---
    etc_machine_id = FactMapper("etc_machine_id", str_or_none)
