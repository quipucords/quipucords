"""Test the product JBoss Web Server get_version.

This file is split out of test_product_jws because django.test.TestCase
conflicts with pytest.mark.parametrize.
"""

import pytest

from fingerprinter.jboss_web_server import get_version


@pytest.mark.parametrize(
    "raw,expected",
    (
        # real values from zip files - pattern used since JWS 5.0
        ("Red Hat JBoss Web Server - Version 5.0 SP3", "JWS 5.0.3"),
        ("Red Hat JBoss Web Server - Version 5.3 SP2", "JWS 5.3.2"),
        ("Red Hat JBoss Web Server - Version 6.0 SP5", "JWS 6.0.5"),
        ("Red Hat JBoss Web Server - Version 7.0 GA", "JWS 7.0"),
        ("jws6", "JWS 6.x.x"),
        ("jws7", "JWS 7.x.x"),
        # artificial values following the same pattern
        ("Red Hat JBoss Web Server - Version 17.0 GA", "JWS 17.0"),
        ("Red Hat JBoss Web Server - Version 7.10 GA", "JWS 7.10"),
        ("Red Hat JBoss Web Server - Version 5.13 SP2", "JWS 5.13.2"),
        ("Red Hat JBoss Web Server - Version 6.0 SP15", "JWS 6.0.15"),
        ("jws19", "JWS 19.x.x"),
        # all these values used to exist in static map JWS_CLASSIFICATIONS
        # we add them here to ensure backwards compatibility
        ("JWS_3.0.1", "JWS 3.0.1"),
        ("JWS_3.0.2", "JWS 3.0.2"),
        ("JWS_3.0.3", "JWS 3.0.3"),
        ("JWS_3.1.0", "JWS 3.1.0"),
        ("JWS_3.1.1", "JWS 3.1.1"),
        ("JWS_3.1.2", "JWS 3.1.2"),
        ("JWS_3.1.3", "JWS 3.1.3"),
        ("JWS_3.1.4", "JWS 3.1.4"),
        ("JWS_3.1.5", "JWS 3.1.5"),
        ("JWS_3.1.6", "JWS 3.1.6"),
        ("JWS_3.1.7", "JWS 3.1.7"),
        ("JWS_3.1.8", "JWS 3.1.8"),
        ("JWS_3.1.9", "JWS 3.1.9"),
        ("Red Hat JBoss Web Server - Version 5.0 GA", "JWS 5.0"),
        ("Red Hat JBoss Web Server - Version 5.0.0 GA", "JWS 5.0.0"),
        ("jws5", "JWS 5.x.x"),
        ("Red Hat JBoss Web Server - Version 5.1 GA", "JWS 5.1"),
        ("Red Hat JBoss Web Server - Version 5.1.0 GA", "JWS 5.1.0"),
        ("Red Hat JBoss Web Server - Version 5.2 GA", "JWS 5.2"),
        ("Red Hat JBoss Web Server - Version 5.2.0 GA", "JWS 5.2.0"),
        ("Red Hat JBoss Web Server - Version 5.3 GA", "JWS 5.3"),
        # the commented one below used to be in a map, but it is inconsistent
        # with earlier three-digit GA. Keeping it here for reference,
        # but unless we want to special-case 5.3.0 only, let's just handle
        # them all the same way.
        # Minor versions of JWS do not receive extra support (like RHEL does).
        # JWS 5.x has ELS2 until end of 2030, but that means 5.8.x
        # ("Red Hat JBoss Web Server - Version 5.3.0 GA", "JWS 5.3"),
        ("Red Hat JBoss Web Server - Version 5.3.0 GA", "JWS 5.3.0"),
        ("Red Hat JBoss Web Server - Version 5.3.1 GA", "JWS 5.3.1"),
    ),
)
def test_get_version(raw, expected):
    """Test the get_version function."""
    versions = get_version([raw])

    assert versions == [expected]


@pytest.mark.parametrize(
    "raw",
    (
        "jws 5",
        "jws5-standalone",
        "JWS_2.1.0",
        "Red Hat JBoss Web Server Version 7.0 GA",
        "Red Hat JBoss Web Server Version 5.0 SP3",
        "Red Hat JBoss Web Server - Version 5.3.2",
        "Red Hat JBoss Web Server - Version 6.0SP5",
        "Red Hat JBoss Web Server - Version 7.0GA",
        "This one ain't even trying",
    ),
)
def test_get_version_negative(raw):
    """Test things that could be mistaken for JWS version."""
    versions = get_version([raw])

    assert versions == []
