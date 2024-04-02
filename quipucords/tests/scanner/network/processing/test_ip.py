"""Unit tests for process `ip address show` facts."""

from scanner.network.processing import ip
from scanner.network.processing.util_for_test import ansible_result

IP_LOOPBACK_OUTPUT_TEMPLATE = """\
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
"""  # noqa: E501

IP_ETHERNET_OUTPUT_TEMPLATE = """\
{sequence_number}: eth{interface_number}: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9001 qdisc fq_codel state UP group default qlen 1000
    link/ether {mac_address} brd {mac_broadcast}
    altname enX{interface_number}
    inet {ipv4_address}/20 brd {ipv4_broadcast} scope global dynamic noprefixroute eth0
       valid_lft 2380sec preferred_lft 2380sec
    inet6 {ipv6_address}/64 scope link
       valid_lft forever preferred_lft forever
"""  # noqa: E501


def synthesize_eth_output(
    faker,
    sequence_number=2,
    interface_number=0,
    ipv4_address=None,
    mac_address=None,
):
    """Synthesize a single eth# interface's output from `ip address show`."""
    if not ipv4_address:
        ipv4_address = faker.ipv4_private()
    if not mac_address:
        mac_address = faker.mac_address()
    ipv4_broadcast = faker.ipv4_private()
    mac_broadcast = faker.mac_address()
    ipv6_address = faker.ipv6()
    return IP_ETHERNET_OUTPUT_TEMPLATE.format(
        sequence_number=sequence_number,
        interface_number=interface_number,
        ipv4_address=ipv4_address,
        ipv4_broadcast=ipv4_broadcast,
        mac_address=mac_address,
        mac_broadcast=mac_broadcast,
        ipv6_address=ipv6_address,
    )


def test_single_ipv4_address(faker):
    """Test extracting a single IPv4 address."""
    ipv4_address = faker.ipv4_private()
    ip_command_output = IP_LOOPBACK_OUTPUT_TEMPLATE
    ip_command_output += synthesize_eth_output(faker, ipv4_address=ipv4_address)
    result = ip.ProcessIpAddressesIPv4.process(ansible_result(ip_command_output))
    assert result == [ipv4_address]


def test_multiple_ipv4_addresses(faker):
    """Test extracting multiple IPv4 addresses."""
    ipv4_addresses = [
        faker.ipv4_private(),
        faker.ipv4_private(),
        faker.ipv4_private(),
    ]
    ip_command_output = IP_LOOPBACK_OUTPUT_TEMPLATE
    for offset, ipv4_address in enumerate(ipv4_addresses):
        ip_command_output += synthesize_eth_output(
            faker,
            sequence_number=2 + offset,
            interface_number=offset,
            ipv4_address=ipv4_address,
        )
    result = ip.ProcessIpAddressesIPv4.process(ansible_result(ip_command_output))
    assert set(result) == set(ipv4_addresses)


def test_invalid_ipv4_address(faker):
    """
    Test ignoring an invalid IPv4 address.

    Under normal curcumstances, this should not be possible because `ip` should not
    output invalid addresses.
    """
    invalid_ipv4_address = faker.slug()
    ip_command_output = IP_LOOPBACK_OUTPUT_TEMPLATE
    ip_command_output += synthesize_eth_output(faker, ipv4_address=invalid_ipv4_address)
    result = ip.ProcessIpAddressesIPv4.process(ansible_result(ip_command_output))
    assert result == []


def test_one_invalid_among_several_normal_ipv4_addresses(faker):
    """
    Test ignoring an invalid IPv4 address but still finding other valid addresses.

    Under normal curcumstances, this should not be possible because `ip` should not
    output invalid addresses.
    """
    invalid_ipv4_address = faker.slug()
    good_ipv4_addresses = [
        faker.ipv4_private(),
        faker.ipv4_private(),
        faker.ipv4_private(),
    ]
    all_addresses = (
        # Put the bad address in the middle of the good addresses.
        good_ipv4_addresses[:1]
        + [invalid_ipv4_address]
        + good_ipv4_addresses[1:]
    )
    ip_command_output = IP_LOOPBACK_OUTPUT_TEMPLATE
    for offset, ipv4_address in enumerate(all_addresses):
        ip_command_output += synthesize_eth_output(
            faker,
            sequence_number=2 + offset,
            interface_number=offset,
            ipv4_address=ipv4_address,
        )
    result = ip.ProcessIpAddressesIPv4.process(ansible_result(ip_command_output))
    assert set(result) == set(good_ipv4_addresses)


def test_single_mac_address(faker):
    """Test extracting a single MAC address."""
    mac_address = faker.mac_address()
    ip_command_output = IP_LOOPBACK_OUTPUT_TEMPLATE
    ip_command_output += synthesize_eth_output(faker, mac_address=mac_address)
    result = ip.ProcessIpAddressesMAC.process(ansible_result(ip_command_output))
    assert result == [mac_address]


def test_multiple_mac_addresses(faker):
    """Test extracting multiple MAC addresses."""
    mac_addresses = [
        faker.mac_address(),
        faker.mac_address(),
        faker.mac_address(),
    ]
    ip_command_output = IP_LOOPBACK_OUTPUT_TEMPLATE
    for offset, mac_address in enumerate(mac_addresses):
        ip_command_output += synthesize_eth_output(
            faker,
            sequence_number=2 + offset,
            interface_number=offset,
            mac_address=mac_address,
        )
    result = ip.ProcessIpAddressesMAC.process(ansible_result(ip_command_output))
    assert set(result) == set(mac_addresses)


def test_invalid_mac_address(faker):
    """
    Test ignoring an invalid MAC address.

    Under normal curcumstances, this should not be possible because `ip` should not
    output invalid addresses.
    """
    invalid_mac_address = faker.slug()
    ip_command_output = IP_LOOPBACK_OUTPUT_TEMPLATE
    ip_command_output += synthesize_eth_output(faker, mac_address=invalid_mac_address)
    result = ip.ProcessIpAddressesMAC.process(ansible_result(ip_command_output))
    assert result == []


def test_one_invalid_among_normal_mac_addresses(faker):
    """
    Test ignoring an invalid MAC address but still finding other valid addresses.

    Under normal curcumstances, this should not be possible because `ip` should not
    output invalid addresses.
    """
    invalid_mac_address = faker.slug()
    good_mac_addresses = [
        faker.mac_address(),
        faker.mac_address(),
    ]
    all_addresses = (
        # Put the bad address in the middle of the good addresses.
        good_mac_addresses[:1]
        + [invalid_mac_address]
        + good_mac_addresses[1:]
    )
    ip_command_output = IP_LOOPBACK_OUTPUT_TEMPLATE
    for offset, mac_address in enumerate(all_addresses):
        ip_command_output += synthesize_eth_output(
            faker,
            sequence_number=2 + offset,
            interface_number=offset,
            mac_address=mac_address,
        )
    result = ip.ProcessIpAddressesMAC.process(ansible_result(ip_command_output))
    assert set(result) == set(good_mac_addresses)
