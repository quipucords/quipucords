"""normalizer for network scans."""

import ipaddress

from api.deployments_report.model import SystemFingerprint
from constants import DataSources
from fingerprinter import formatters
from scanner.network.utils import is_valid_ipv4_address, is_valid_ipv6_address
from scanner.normalizer import BaseNormalizer, FactMapper, NormalizedResult
from utils import deepget


def infrastructure_type_normalizer(
    *, virt_what=None, hostnamectl=None, subman_virt_is_guest=None
):
    """
    Normalize infrastructure type.

    IMPORTANT DEVELOPER NOTE: This function's implementation largely duplicates the code
    originally written in fingerprinter.runner.fingerprint_network_infrastructure_type,
    but this code has never been tested in a true end-to-end integration test, and at
    the time of this writing, we don't really know if this works as advertised.

    TODO FIXME: Verify that this actually works when we switch to the new normalizers.
    """
    virt_what: list[str] | None = deepget(virt_what, "value")
    hostnamectl_chassis: str | None = deepget(hostnamectl, "value__chassis")

    if virt_what:
        # We assume *anything* in virt-what's stdout means virtualized.
        raw_fact_key = "virt_what"
        fact_value = SystemFingerprint.VIRTUALIZED
    elif subman_virt_is_guest:
        # We don't know virt_type, but subscription-manager says it's a guest.
        # So, we assume it's virtualized. See also: DISCOVERY-243.
        raw_fact_key = "subman_virt_is_guest"
        fact_value = SystemFingerprint.VIRTUALIZED
    elif hostnamectl_chassis in ["vm", "container"]:
        # If we could not find relevant details from virt_what, we fall back to
        # checking hostnamtctl output. See also: DISCOVERY-428.
        raw_fact_key = "hostnamectl"
        fact_value = SystemFingerprint.VIRTUALIZED
    elif hostnamectl_chassis:
        raw_fact_key = "hostnamectl"
        fact_value = SystemFingerprint.BARE_METAL
    else:
        raw_fact_key = "virt_what"
        fact_value = SystemFingerprint.UNKNOWN
    return NormalizedResult(fact_value, raw_fact_keys=[raw_fact_key])


def ip_address_normalizer(ifconfig_ip_addresses: list[str]):
    """Normalize ip_address."""
    # https://github.com/quipucords/quipucords/blob/e65d0e3deb23adca41ceed701e4d002187e593f6/quipucords/api/common/entities.py#L124-L136
    if ifconfig_ip_addresses is None:
        return []
    addresses = []
    for raw_ip in ifconfig_ip_addresses:
        ip_addr = ipaddress.ip_address(raw_ip)
        # raw fact collects ipv4 and ipv6 addresses
        if isinstance(ip_addr, ipaddress.IPv4Address) or isinstance(
            ip_addr, ipaddress.IPv6Address
        ):
            addresses.append(str(ip_addr))
    return addresses


def network_interfaces(ip_addresses: list[str]):
    """Normalize network interfaces."""
    ipv4_addresses = ipv6_addresses = []
    for ip_address in ip_addresses:
        if is_valid_ipv4_address(ip_address):
            ipv4_addresses.append(ip_address)
        elif is_valid_ipv6_address(ip_address):
            ipv6_addresses.append(ip_address)
    interface = {
        "name": "unknown",  # required by yuptoo
        "ipv4_addresses": ipv4_addresses,
        "ipv6_addresses": ipv6_addresses,
    }
    return [interface]


class Normalizer(BaseNormalizer):
    """Network Scan normalizer."""

    source_type = DataSources.NETWORK.value

    mac_addresses = FactMapper(
        "ifconfig_mac_addresses", formatters.format_mac_addresses
    )
    ip_addresses = FactMapper("ifconfig_ip_addresses", ip_address_normalizer)
    bios_uuid = FactMapper("dmi_system_uuid", formatters.str_or_none)
    insights_id = FactMapper("insights_client_id", formatters.str_or_none)
    subscription_manager_id = FactMapper(
        "subscription_manager_id", formatters.str_or_none
    )
    number_of_cpus = FactMapper("cpu_core_count", int)
    number_of_sockets = FactMapper("cpu_socket_count", int)
    cores_per_socket = FactMapper("cpu_core_per_socket", int)
    system_memory_bytes = FactMapper("system_memory_bytes", int)
    infrastructure_type = FactMapper(
        ["virt_what", "subman_virt_is_guest", "hostnamectl"],
        infrastructure_type_normalizer,
    )
    infrastructure_vendor = FactMapper("virt_type", formatters.str_or_none)
    os_release = FactMapper("etc_release_release", formatters.str_or_none)
    arch = FactMapper("uname_processor", formatters.str_or_none)
    cloud_provider = FactMapper("cloud_provider", formatters.str_or_none)
    system_purpose = FactMapper("system_purpose_json", dict)
    network_interfaces = FactMapper(
        None, network_interfaces, dependencies=["ip_addresses"]
    )
    etc_machine_id = FactMapper("etc_machine_id", formatters.str_or_none)
