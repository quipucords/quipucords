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
