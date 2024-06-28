"""Test the fingerprinter.runner module."""

import pytest
from faker import Faker

from api.deployments_report.model import SystemFingerprint
from fingerprinter import runner

_faker = Faker()


@pytest.mark.parametrize(
    "facts,expected_raw_fact_key,expected_fact_value",
    (
        (
            {"virt_what_type": "bare metal"},
            "virt_what_type",
            SystemFingerprint.BARE_METAL,
        ),
        (
            {"virt_what_type": _faker.slug(), "virt_type": True},
            "virt_type",
            SystemFingerprint.VIRTUALIZED,
        ),
        (
            {
                "virt_what_type": _faker.slug(),
                "virt_type": False,
                "subman_virt_is_guest": True,
            },
            "subman_virt_is_guest",
            SystemFingerprint.VIRTUALIZED,
        ),
        (
            {
                "virt_what_type": _faker.slug(),
                "virt_type": False,
                "hostnamectl": {"value": {"chassis": "vm"}},
            },
            "hostnamectl",
            SystemFingerprint.VIRTUALIZED,
        ),
        (
            {
                "virt_what_type": _faker.slug(),
                "virt_type": False,
                "hostnamectl": {"value": {"chassis": "potato"}},
            },
            "hostnamectl",
            SystemFingerprint.BARE_METAL,
        ),
        (
            {
                "virt_what_type": _faker.slug(),
                "virt_type": False,
                "hostnamectl_chassis": {},
            },
            "virt_what_type",
            SystemFingerprint.UNKNOWN,
        ),
        (
            {
                "virt_type": False,
                "hostnamectl_chassis": {},
            },
            "virt_what_type/virt_type",
            SystemFingerprint.UNKNOWN,
        ),
    ),
)
def test_fingerprint_network_infrastructure_type(
    facts, expected_raw_fact_key, expected_fact_value
):
    """Test fingerprinting infrastructure_type from network scan facts."""
    raw_fact_key, fact_value = runner.fingerprint_network_infrastructure_type(facts)
    assert raw_fact_key == expected_raw_fact_key
    assert fact_value == expected_fact_value
