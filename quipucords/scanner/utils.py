"""Shared utilities for all scanner types."""

import ipaddress


def format_host_for_url(host: str) -> str:
    """Wrap IPv6 addresses in brackets for proper URL formatting.

    Per RFC 2732, IPv6 addresses in URLs must be enclosed in square brackets
    to distinguish the address colons from the port separator.

    Example:
        - "192.168.1.1" -> "192.168.1.1" (unchanged)
        - "fd00:dead:beef::126" -> "[fd00:dead:beef::126]"
        - "api.example.com" -> "api.example.com" (unchanged)

    :param host: Hostname, IPv4 address, or IPv6 address
    :returns: The host, with IPv6 addresses wrapped in brackets
    """
    try:
        ip = ipaddress.ip_address(host)
        if isinstance(ip, ipaddress.IPv6Address):
            return f"[{host}]"
    except ValueError:
        pass
    return host
