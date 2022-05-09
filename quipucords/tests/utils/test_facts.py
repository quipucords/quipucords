# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test facts helpers."""

import pytest

from tests.utils.facts import fact_expander


@pytest.mark.parametrize(
    "raw_fact_name,expected_result",
    [
        ("foo", {"foo"}),
        ("foo__bar", {"foo"}),
        ("foo/bar", {"foo", "bar"}),
        ("foo/bar__some_internal", {"foo", "bar"}),
        ("foo__a/bar", {"foo", "bar"}),
    ],
)
def test_fact_expander(raw_fact_name, expected_result):
    """Test fact_expander helper."""
    assert fact_expander(raw_fact_name) == expected_result
