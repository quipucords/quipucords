"""normalizer for network scans."""

import ipaddress

from constants import DataSources
from fingerprinter import formatters
from scanner.normalizer import BaseNormalizer, FactMapper


def infrastructure_type_normalizer(*, virt_what_type, virt_type):
    """Normalize infrastructure type."""
    # https://github.com/quipucords/quipucords/blob/e65d0e3deb23adca41ceed701e4d002187e593f6/quipucords/api/common/entities.py#L92-L112
    if virt_what_type == "bare metal":
        return "physical"
    elif virt_type or virt_what_type:
        return "virtualized"
    return "unknown"


def ip_address_normalizer(ifconfig_ip_addresses: list[str]):
    """Normalize ip_address."""
    # https://github.com/quipucords/quipucords/blob/e65d0e3deb23adca41ceed701e4d002187e593f6/quipucords/api/common/entities.py#L124-L136
    if ifconfig_ip_addresses is None:
        return None
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
        "ipv4_addresses": ip_addresses,
        "ipv6_addresses": [],  # required by yuptoo
    }
    return [interface]


class Normalizer(BaseNormalizer):
    """Network Scan normalizer."""

    source_type = DataSources.NETWORK.value

    mac_addresses = FactMapper(
        "ifconfig_mac_addresses", formatters.format_mac_addresses
    )
    ip_addresses = FactMapper("ifconfig_ip_addresses", ip_address_normalizer)
    bios_uuid = FactMapper("dmi_system_uuid", str)
    insights_id = FactMapper("insights_client_id", str)
    # satellite_id = FactMapper("_rawfact_", fn)
    subscription_manager_id = FactMapper("subscription_manager_id", str)
    # provider_id = FactMapper("_rawfact_", fn)
    # provider_type = FactMapper("_rawfact_", fn)
    number_of_cpus = FactMapper("cpu_core_count", int)
    number_of_sockets = FactMapper("cpu_socket_count", int)
    cores_per_socket = FactMapper("cpu_core_per_socket", int)
    system_memory_bytes = FactMapper("system_memory_bytes", int)
    infrastructure_type = FactMapper(
        ["virt_what_type", "virt_type"],
        infrastructure_type_normalizer,
    )
    # infrastructure_vendor = FactMapper("_rawfact_", fn)
    os_release = FactMapper("etc_release_release", str)
    arch = FactMapper("uname_processor", str)
    cloud_provider = FactMapper("cloud_provider", str)
    system_purpose = FactMapper("system_purpose_json", lambda x: x)
    network_interfaces = FactMapper(
        None, network_interfaces, dependencies=["ip_addresses"]
    )
    # ----- non canonical/system profile facts ---
    etc_machine_id = FactMapper("etc_machine_id", str)
