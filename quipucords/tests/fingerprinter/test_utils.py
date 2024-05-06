"""Tests for fingerprint.utils module."""

import pytest

from fingerprinter.utils import product_entitlement_found


@pytest.mark.parametrize(
    "entitlements,product_name,found",
    [
        [[{"name": "foo"}], "foo", True],
        [[{"name": "long name with foo in the middle"}], "foo", True],
        [[{"name": "bar"}], "foo", False],
        [[{"name": None}], "foo", False],
        [[{"nombre": "foo"}], "foo", False],
        [[{}], "foo", False],
    ],
)
def test_product_entitlement_found(
    entitlements: list[dict], product_name: str, found: bool
):
    """Test product_entitlement_found function."""
    assert product_entitlement_found(entitlements, product_name) == found
