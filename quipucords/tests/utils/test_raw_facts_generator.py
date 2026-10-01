"""Test raw facts generator helpers."""

import pytest

from tests.utils.raw_facts_generator import fake_installed_products, fake_rhel_version

BASE = {
    "id": "479",
    "name": "Red Hat Enterprise Linux for x86_64",
    "version": "10.2",
    "arch": "x86_64",
    "tags": ["rhel-10", "rhel-10-x86_64"],
}
ADDON = {
    "id": "83",
    "name": "Red Hat Enterprise Linux High Availability",
    "version": "10.2",
    "arch": "x86_64",
    "tags": ["rhel-10-highavailability"],
}


@pytest.mark.parametrize(
    "installed_products,expected",
    [
        ([BASE], "10.2"),
        ([BASE, ADDON], "10.2"),
        # product certs come back in filesystem order; the base one is not
        # guaranteed to be first
        ([ADDON, BASE], "10.2"),
        ([ADDON], None),
        ([{**BASE, "tags": []}], None),
        ([{**BASE, "version": None}], None),
        ([], None),
        (None, None),
    ],
    ids=[
        "base-only",
        "base-first",
        "base-last",
        "add-on-only",
        "no-tags",
        "no-version",
        "empty-list",
        "none",
    ],
)
def test_fake_rhel_version(installed_products, expected):
    """Test the base operating system is found by tag, not by position."""
    assert fake_rhel_version(installed_products) == expected


def test_fake_rhel_version_matches_fake_installed_products():
    """Test generated products always yield a resolvable rhel version."""
    installed_products = fake_installed_products()
    version = fake_rhel_version(installed_products)
    assert version is not None
    assert version in {product["version"] for product in installed_products}
