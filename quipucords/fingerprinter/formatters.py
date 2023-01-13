# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Fingerprint formatters."""


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


def convert_architecture(architecture):
    """Convert architecture name."""
    architecture_map = {"amd64": "x86_64"}
    if not architecture_map.get(architecture):
        return architecture
    return architecture_map.get(architecture)
