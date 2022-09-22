# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test asserts module."""

import pytest

from tests.asserts import assert_elements_type


def test_assert_elements_type_success():
    """Test green path for assert_elements_type."""
    assert_elements_type(list("abc"), str)


def test_assert_elements_type_failure():
    """Test failure for assert_elements_type."""
    with pytest.raises(AssertionError):
        assert_elements_type([1, 2, "3"], int)
