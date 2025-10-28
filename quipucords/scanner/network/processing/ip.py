"""Process the raw output from the "ip" role.

These methods expect the `ip` command output to fit a very specific pattern.
If we ever observe different forms of output, we must update this code.
Here is an example output (from a RHEL9 VM) that this processor can handle:

1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9001 qdisc fq_codel state UP group default qlen 1000
    link/ether 06:c5:af:85:83:e1 brd ff:ff:ff:ff:ff:ff
    altname enX0
    inet 172.31.64.28/20 brd 172.31.79.255 scope global dynamic noprefixroute eth0
       valid_lft 2380sec preferred_lft 2380sec
    inet6 fe80::4c4:ffaf:f5e8:3e81/64 scope link
       valid_lft forever preferred_lft forever
"""  # noqa: E501

import re

from scanner.network.processing import process
from scanner.network.utils import is_valid_ipv4_address, is_valid_ipv6_address

EXCLUDE_IPV4_ADDRESSES = {"127.0.0.1", "0.0.0.0"}  # noqa: S104
EXCLUDE_IPV6_ADDRESSES = {"::1"}
EXCLUDE_MAC_ADDRESSES = {"00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff"}
MATCH_MAC_ADDRESS = re.compile("^[0-9a-f]{2}(?::[0-9a-f]{2}){5}$")


def is_valid_mac_address(address: str):
    """Return True if the provided string is a valid MAC address."""
    return re.match(MATCH_MAC_ADDRESS, address) is not None


class ProcessIpAddressesIPv4(process.Processor):
    """Process the IPv4 addresses from `ip address show`."""

    KEY = "ip_address_show_ips"

    @staticmethod
    def process(output: dict, dependencies=None) -> list[str]:
        """
        Extract IPv4 addresses from the raw `ip address show` output.

        This handles output lines that look like this:

            inet 172.31.64.28/20 brd 172.31.79.255 scope

        to extract and return ["172.31.64.28"].
        """
        lines = [line.lstrip() for line in output["stdout_lines"]]
        ipv4_addresses = {
            line.strip().split(" ")[1].split("/")[0]
            for line in lines
            if line.startswith("inet ")
        } - EXCLUDE_IPV4_ADDRESSES
        return list(filter(is_valid_ipv4_address, ipv4_addresses))


class ProcessIpAddressesIPv6(process.Processor):
    """Process the IPv6 addresses from `ip address show`."""

    KEY = "ip_address_show_ips"

    @staticmethod
    def process(output: dict, dependencies=None) -> list[str]:
        """
        Extract IPv4 addresses from the raw `ip address show` output.

        This handles output lines that look like this:

            inet6 fe80::20c:29ff:feac:4355/64 scope link noprefixroute

        to extract and return ["fe80::20c:29ff:feac:4355"]
        """
        lines = [line.lstrip() for line in output["stdout_lines"]]
        ipv6_addresses = {
            line.strip().split(" ")[1].split("/")[0]
            for line in lines
            if line.startswith("inet6 ")
        } - EXCLUDE_IPV6_ADDRESSES
        return list(filter(is_valid_ipv6_address, ipv6_addresses))


class ProcessIpAddressesMAC(process.Processor):
    """Process the MAC addresses from `ip address show`."""

    KEY = "ip_address_show_mac"

    @staticmethod
    def process(output: dict, dependencies=None) -> list[str]:
        """
        Extract MAC addresses from the raw `ip address show` output.

        This handles output lines that look like this:

            link/ether 06:c5:af:85:83:e1 brd ff:ff:ff:ff:ff:ff

        to extract and return ["06:c5:af:85:83:e1"].
        """
        lines = [line.lstrip() for line in output["stdout_lines"]]
        mac_addresses = (
            set(
                line.strip().split(" ")[1].split("/")[0]
                for line in lines
                if line.startswith("link/")
            )
            - EXCLUDE_MAC_ADDRESSES
        )
        return list(filter(is_valid_mac_address, mac_addresses))
