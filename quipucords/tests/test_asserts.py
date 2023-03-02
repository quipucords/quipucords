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
