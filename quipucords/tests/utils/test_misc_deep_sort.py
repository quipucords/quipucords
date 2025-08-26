"""Test utils.misc.deep_sort function."""

import pytest

from utils.misc import deep_sort


@pytest.mark.parametrize(
    "value,expected_result",
    [
        (1, 1),
        (None, None),
        ("hello", "hello"),
        (["foo", "bar"], ["bar", "foo"]),
        (("foo", "bar"), ["bar", "foo"]),
        ({"foo", "bar"}, ["bar", "foo"]),
        ([1, False, 3.14], [False, 1, 3.14]),
        (
            {"foo": {"fizz": "ok", "buzz": {2, 1}}, "bar": (1, False)},
            {"bar": [False, 1], "foo": {"buzz": [1, 2], "fizz": "ok"}},
        ),
        ({"foo": (2, 1), "bar": None}, {"bar": None, "foo": [1, 2]}),
    ],
)
def test_deep_sort(value, expected_result):
    """Test deep_sort actually sorts and sorts deeply."""
    assert deep_sort(value) == expected_result
