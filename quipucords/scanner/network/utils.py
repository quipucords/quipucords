"""Scanner used for host connection discovery."""

import ipaddress
from functools import cache

import yaml
from ansible.errors import AnsibleError
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.inventory import detect_range, expand_hostname_range
from django.conf import settings

from api.vault import decrypt_data_as_unicode
from constants import GENERATED_SSH_KEYFILE


def _credential_vars(credential: dict) -> dict:
    """Build a dictionary containing cred information."""
    ansible_dict = {}
    username = credential.get("username")
    password = credential.get("password")
    # TODO: remove the deprecated ssh_keyfile from Credential model
    ssh_keyfile = credential.get(GENERATED_SSH_KEYFILE) or credential.get("ssh_keyfile")
    become_method = credential.get("become_method")
    become_user = credential.get("become_user")
    become_password = credential.get("become_password")

    ansible_dict["ansible_user"] = username
    if password:
        ansible_dict["ansible_ssh_pass"] = decrypt_data_as_unicode(password)
    if ssh_keyfile:
        ansible_dict["ansible_ssh_private_key_file"] = ssh_keyfile
    if become_password:
        ansible_dict["ansible_become_pass"] = decrypt_data_as_unicode(become_password)
    if become_method:
        ansible_dict["ansible_become_method"] = become_method
    if become_user:
        ansible_dict["ansible_become_user"] = become_user
    return ansible_dict


def _construct_vars(connection_port, credential: dict = None) -> dict:
    """Get the Ansible host vars that implement a credential.

    :param connection_port: The connection port
    :param credential: The credential used for connections
    :returns: a dict that can be used as the host variables in an
        Ansible inventory.
    """
    ansible_vars = {"ansible_port": connection_port}

    if credential is not None:
        ansible_dict = _credential_vars(credential)
        ansible_vars.update(ansible_dict)

    return ansible_vars


def construct_inventory(
    hosts: list,
    connection_port,
    concurrency_count: int,
    *,
    credential: dict = None,
    exclude_hosts: list | None = None,
) -> tuple[list[str], dict]:
    """Create a dictionary inventory for Ansible to execute with.

    :param hosts: The collection of hosts (or hosts/credential tuples)
    :param credential: The credential used for connections
    :param connection_port: The connection port
    :param concurrency_count: The number of concurrent scans
    :param exclude_hosts: Optional. Hosts to exclude test connections
    :returns: A dictionary of the ansible inventory
    """
    if exclude_hosts is not None:
        hosts = list(set(hosts) - set(exclude_hosts))
    concurreny_groups = [
        hosts[i : i + concurrency_count]
        for i in range(0, len(hosts), concurrency_count)
    ]
    vars_dict = _construct_vars(connection_port, credential)
    children = {}
    group_names = []
    inventory = {"all": {"children": children, "vars": vars_dict}}
    for index, group in enumerate(concurreny_groups):
        group_name = f"group_{index}"
        group_names.append(group_name)
        children[group_name] = {"hosts": _format_hosts_dict(group)}
    return group_names, inventory


def _format_hosts_dict(group) -> dict:
    hosts_dict = {}
    for host in group:
        host_name, host_vars = _get_host_vars(host)
        hosts_dict[host_name] = host_vars
    return hosts_dict


def _get_host_vars(host):
    if not isinstance(host, str):
        # if its not str, we assume it's a tuple host/credentials
        host, credentials = host
        host_vars = _credential_vars(credentials)
    else:
        host_vars = {}
    host_vars["ansible_host"] = host
    return host, host_vars


def _expand_cidr(pattern: str) -> list[str] | None:
    """Expand CIDR notation to list of IPs, or None if not a CIDR."""
    if "/" not in pattern:
        return None
    try:
        network = ipaddress.ip_network(pattern, strict=False)
        return [str(ip) for ip in network.hosts()]
    except ValueError:
        return None


def _expand_ansible_range(pattern: str) -> list[str] | None:
    """Expand Ansible [x:y] range to list of hosts, or None if not a range."""
    if not detect_range(pattern):
        return None
    try:
        return expand_hostname_range(pattern)
    except AnsibleError:
        return None


def _strip_port(hostpattern: str) -> str:
    """Remove port specification from host pattern if present."""
    try:
        pattern, _ = parse_address(hostpattern, allow_ranges=True)
        return pattern
    except AnsibleError:
        return hostpattern


def expand_hostpattern(hostpattern: str) -> list[str]:
    """Expand a host pattern into list of hostnames.

    Handles CIDR notation, Ansible [x:y] ranges, and plain hostnames.

    :param hostpattern: a single host pattern
    :returns: list of hostnames
    """
    # CIDR takes priority (must check before stripping port)
    if expanded := _expand_cidr(hostpattern):
        return expanded

    pattern = _strip_port(hostpattern)

    if expanded := _expand_ansible_range(pattern):
        return expanded

    return [pattern]


def _yaml_load(path_obj):
    return yaml.load(path_obj.open(), Loader=yaml.SafeLoader)


def collect_all_fact_names():
    """Collect all fact names set on ansible playbooks."""
    network_runner_path = settings.BASE_DIR / "scanner/network/runner"
    for playbook in network_runner_path.glob("roles/*/tasks/main.yml"):
        task_list = _yaml_load(playbook)
        for task in task_list:
            yield from task.get("set_fact", {}).keys()


@cache
def get_fact_names():
    """List fact names set on ansible rules."""
    return list(sorted(collect_all_fact_names()))


def raw_facts_template():
    """Results template for fact collection on network scans."""
    return {fact_name: None for fact_name in get_fact_names()}


def is_valid_ipv4_address(address: str):
    """Return True if the provided string is a valid IPv4 address."""
    try:
        ipaddress.IPv4Address(address)
        return True
    except ipaddress.AddressValueError:
        return False


def is_valid_ipv6_address(address: str):
    """Return True if the provided string is a valid IPv6 address."""
    try:
        ipaddress.IPv6Address(address)
        return True
    except ipaddress.AddressValueError:
        return False


def get_ipv4_ipv6_addresses(ip_addresses: list[str]):
    """Given a list of IPv4 and IPv6 addresses, return them as separate lists."""
    ipv4_addresses = []
    ipv6_addresses = []
    for ip_address in ip_addresses:
        if is_valid_ipv4_address(ip_address):
            ipv4_addresses.append(ip_address)
        elif is_valid_ipv6_address(ip_address):
            ipv6_addresses.append(ip_address)
    return ipv4_addresses, ipv6_addresses
