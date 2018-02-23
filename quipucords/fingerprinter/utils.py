#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Utility functions for system fingerprinting."""

NAME = 'name'


def product_entitlement_found(entitlements, product_name):
    """Search entitlements for presences of product_name.

    :param entitlements: list of entitlement dictionaries
    :param product_name: product name to check in entitlements
    :returns: True if found, False otherwise
    """
    for entitlement in entitlements:
        name = entitlement.get(NAME)
        if product_name in name:
            return True
    return False


def strip_prefix(string, prefix):
    """Remove a prefix from a string, if present.

    :param string: the string to operate on.
    :param prefix: the prefix to remove.
    :returns: string without prefix, if prefix was present.
    """
    if string.startswith(prefix):
        return string[len(prefix):]

    return string


def strip_suffix(string, suffix):
    """Remove a suffix from a string, if present.

    :param string: the string to operate on.
    :param suffix: the suffix to remove.
    :returns: string without suffix, if suffix was present.
    """
    if string.endswith(suffix):
        return string[:-len(suffix)]

    return string
