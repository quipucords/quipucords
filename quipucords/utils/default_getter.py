# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Module for default_getter function."""

from typing import Any, Hashable


def default_getter(data: dict, key: Hashable, default_value: Any) -> Any:
    """Get value from dict with a default value if it does not exist or is None."""
    val = data.get(key, default_value)
    if val is None:
        return default_value
    return val
