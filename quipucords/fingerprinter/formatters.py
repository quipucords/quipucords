# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Fingerprint formatters."""

import re


def format_mac_addresses(mac_addresses):
    """Format mac addresess."""
    if isinstance(mac_addresses, list):
        mac_addresses = list(map(lambda x: x.lower(), mac_addresses))
    return mac_addresses


def is_redhat_from_vm_os(vcenter_os_release):
    """Determine whether a system is rhel or not base on vcenter vm.os fact."""
    if vcenter_os_release != "" and vcenter_os_release is not None:
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


def convert_memory_fact_to_bytes(memory_capacity):
    binary_unit = re.compile("^\d+([KMG]i)$")
    try:
        m = binary_unit.match(memory_capacity)
    except:
        return memory_capacity
    if not m:
        return memory_capacity
    power = {
        "Ki": 1,
        "Mi": 2,
        "Gi": 3,
    }[m.group(1)]
    return int(memory_capacity.replace(m.group(1), "")) * 1024**power


def extract_ip_addresses(addresses):
    list_ips = []
    for address in addresses:
        if "ip" or "IP" in address["type"]:
            list_ips.append(address["address"])
    return list_ips


def get_node_roles(taints):
    # assuming we are going to follow the taint path to get this info
    node_roles = []
    if taints:
        for taint in taints:
            node_roles.append(taint["key"])
    return node_roles


def is_schedulable(taints) -> bool:
    # assuming we are going to follow the taint path to get this info
    node_effects = []
    if taints:
        for taint in taints:
            node_effects.append(taint["effect"])
    return node_effects


def convert_architecture(architecture):
    # to be impplemented
    # https://kubernetes.io/docs/reference/labels-annotations-taints/#kubernetes-io-arch
    known_arch = {"amd64": "x86_64"}
    return known_arch.get(architecture, architecture)
