# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Fingerprint formatters for OpenShift."""


def extract_ip_addresses(addresses):
    """Extract only ip addresses from list of addresses."""
    ip_addresses = []
    for element in addresses:
        if "ip" in element.get("type").lower():
            ip_addresses.append(element.get("address"))
    return ip_addresses


def infer_node_role(labels: dict):
    """Infer node role based on its labels dict."""
    node_roles = []
    for role in ["worker", "master", "control-plane"]:
        role_label = f"node-role.kubernetes.io/{role}"
        if role_label in labels.keys():
            node_roles.append(role)
    return "/".join(node_roles)
