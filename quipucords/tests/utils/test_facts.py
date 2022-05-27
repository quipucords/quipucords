# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test facts helpers."""

import pytest

from tests.utils.facts import RawFactComparator, fact_expander


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


@pytest.mark.parametrize(
    "fact_1,fact_2",
    (
        ("a", "a"),
        ("a", "a/a"),
        ("a", "a/b"),
        ("b", "a/b"),
        ("a/b", "a/b"),
        ("a__1/b", "a"),
        ("a__1", "a"),
        ("a__1", "a__1"),
        ("a__1", "a__2"),
    ),
)
def test_raw_fact_comparator_match(fact_1, fact_2):
    """Test expected macthes between facts."""
    assert fact_1 == RawFactComparator(fact_2)
    assert RawFactComparator(fact_1) == RawFactComparator(fact_2)
    assert RawFactComparator(fact_1) == fact_2


@pytest.mark.parametrize(
    "fact_1,fact_2",
    (
        ("z", "a"),
        ("z", "a/a"),
        ("z", "a/b"),
        ("z", "a/b"),
        ("z/y", "a/b"),
        ("z__1", "a/b"),
        ("z__1", "a"),
        ("z__1", "1"),
        ("z__1", "a__1"),
    ),
)
def test_raw_fact_comparator_mismatch(fact_1, fact_2):
    """Test expected mismatches between facts."""
    assert fact_1 != RawFactComparator(fact_2)
    assert RawFactComparator(fact_1) != RawFactComparator(fact_2)
    assert RawFactComparator(fact_1) != fact_2


def test_invalid_type():
    """Test comparing a fact with un unsupported type."""
    with pytest.raises(
        TypeError, match=r"'42' is unsupported comparison with facts \(type=int\)"
    ):
        assert RawFactComparator("a") == 42
