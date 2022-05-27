# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test default_getter function."""

import pytest

from utils import default_getter


@pytest.mark.parametrize(
    "data,key,default_value,expected_value",
    [
        ({}, "foo", "bar", "bar"),
        ({"foo": None}, "foo", "bar", "bar"),
        ({"foo": 0}, "foo", "bar", 0),
        ({"foo": ""}, "foo", "bar", ""),
        ({"foo": "blabla"}, "foo", "bar", "blabla"),
    ],
)
def test_default_getter(data, key, default_value, expected_value):
    """Test default_getter."""
    assert default_getter(data, key, default_value) == expected_value
