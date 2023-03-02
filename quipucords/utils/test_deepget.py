"""Tests for deepget function."""

import pytest

from utils import deepget

REACHABLE = "REACHABLE"
UNREACHABLE = "UNREACHABLE"


@pytest.fixture
def test_data():
    """Test data for deepget function."""
    return {
        "dict": {
            "internal_dict": {"foo": "bar"},
            "internal_list": [0, "1", {"foo": "bar"}],
            0: 0,
            1: UNREACHABLE,
            "1": REACHABLE,
            "2": "2",
        },
        "list": [1, "2", {"foo": "bar"}],
        "tuple": (1, "2", {"foo": "bar"}),
        "1": REACHABLE,
        1: UNREACHABLE,
        2: UNREACHABLE,
        "literal": REACHABLE,
        "bool": True,
        "1.1": REACHABLE,
        1.1: UNREACHABLE,
        "1__1": UNREACHABLE,
    }


def test_int_key_is_unsupported(test_data):
    """Test unsupported key type and its error message."""
    assert deepget(test_data, "1") == REACHABLE
    with pytest.raises(
        ValueError, match="path=1 should be a string, not <class 'int'>."
    ):
        deepget(test_data, 1)


@pytest.mark.parametrize("path", ({}, [], 1, 1.1, tuple(), set()))
def test_other_unsupported_paths(path):
    """Ensure unsupported types will raise a value error."""
    with pytest.raises(ValueError):
        deepget({}, path)


def test_float_key_unreachable(test_data):
    """Ensure float keys are unsupported."""
    assert test_data["1.1"] == REACHABLE
    assert test_data[1.1] == UNREACHABLE
    assert deepget(test_data, "1.1") == REACHABLE


@pytest.mark.parametrize(
    "key,expected_result",
    (
        ("1", REACHABLE),
        ("2", None),
        ("dict__0", None),
        ("dict__1", REACHABLE),
        ("dict__2", "2"),
        ("dict__internal_dict", {"foo": "bar"}),
        ("dict__internal_list", [0, "1", {"foo": "bar"}]),
        ("dict__internal_list__0.1", None),
        ("dict__internal_list__0", 0),
        ("dict__internal_list__1", "1"),
        ("dict__internal_list__2", {"foo": "bar"}),
        ("dict__internal_list__2__foo", "bar"),
        ("dict__internal_list__2__foo__bar", None),
        ("dict__internal_list__3", None),
        ("dict__internal_list__a", None),
        ("list", [1, "2", {"foo": "bar"}]),
        ("list__0", 1),
        ("list__1", "2"),
        ("list__2", {"foo": "bar"}),
        ("list__2__foo", "bar"),
        ("list__2__foo__bar", None),
        ("tuple", (1, "2", {"foo": "bar"})),
        ("tuple__0", 1),
        ("tuple__1", "2"),
        ("tuple__2", {"foo": "bar"}),
        ("tuple__2__foo", "bar"),
        ("tuple__2__foo__bar", None),
        ("non-existent", None),
        ("non-existent__1", None),
        ("non-existent__foo__bar", None),
        ("literal", REACHABLE),
        ("literal__1", None),
        ("literal__a", None),
        ("bool", True),
        ("bool__1", None),
        ("bool__a", None),
        ("1.1", REACHABLE),
        ("1__1", None),
        ("0__1__2__3", None),
    ),
)
def test_deepget_with_dict(key, expected_result, test_data):
    """Battery of tests with deepget function."""
    assert deepget(test_data, key) == expected_result
