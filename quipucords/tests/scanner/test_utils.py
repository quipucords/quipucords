"""Test shared scanner utilities."""

import pytest

from scanner.utils import format_host_for_url


@pytest.mark.parametrize(
    "host,expected",
    [
        ("192.168.1.1", "192.168.1.1"),
        ("10.0.0.1", "10.0.0.1"),
        ("fd00:dead:beef::126", "[fd00:dead:beef::126]"),
        ("::1", "[::1]"),
        ("2001:db8::1", "[2001:db8::1]"),
        ("fe80::1%eth0", "[fe80::1%eth0]"),
        ("api.example.com", "api.example.com"),
        ("localhost", "localhost"),
        ("[fd00:dead:beef::126]", "[fd00:dead:beef::126]"),
        ("fd00:dead:beef::126::", "fd00:dead:beef::126::"),
        ("not:a:valid:ipv6", "not:a:valid:ipv6"),
        ("", ""),
    ],
)
def test_format_host_for_url(host, expected):
    """Test that IPv6 addresses are wrapped in brackets."""
    assert format_host_for_url(host) == expected
