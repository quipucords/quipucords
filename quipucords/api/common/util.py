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

"""Util for common operations."""


def is_int(value):
    """Check if a value is convertable to int.

    :param value: The value to convert
    :returns: The int or None if not convertable
    """
    if isinstance(value, int):
        return True

    try:
        int(value)
        return True
    except ValueError:
        return False


def convert_to_int(value):
    """Convert value to in if possible.

    :param value: The value to convert
    :returns: The int or None if not convertable
    """
    if not is_int(value):
        return None
    return int(value)
