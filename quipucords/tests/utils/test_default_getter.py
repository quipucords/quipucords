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
