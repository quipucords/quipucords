"""Scanner used for host connection discovery."""

from functools import cache
from multiprocessing import Value

import yaml
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.inventory import detect_range, expand_hostname_range
from django.conf import settings

from api.models import ScanJob
from api.vault import decrypt_data_as_unicode
from scanner.network.exceptions import NetworkCancelException, NetworkPauseException

# key is stop_type, value is manager_interrupt.value
STOP_STATES = {
    "cancel": ScanJob.JOB_TERMINATE_CANCEL,
    "pause": ScanJob.JOB_TERMINATE_PAUSE,
}


def check_manager_interrupt(interrupt: Value):
    """Check if cancel & pause exception should be raised."""
    if not interrupt:
        return
    if interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
        raise NetworkCancelException()
    if interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
        raise NetworkPauseException()


def _credential_vars(credential):
    """Build a dictionary containing cred information."""
    ansible_dict = {}
    username = credential.get("username")
    password = credential.get("password")
    ssh_keyfile = credential.get("ssh_keyfile")
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


def _construct_vars(connection_port, credential=None):
    """Get the Ansible host vars that implement a credential.

    :param connection_port: The connection port
    :param credential: The credential used for connections
    :returns: a dict that can be used as the host variables in an
        Ansible inventory.
    """
    # ssh arguments for compatibility with defaults for older systems (like RHEL 5&6)
    # (this is only meant to help quipucords running on baremetal since the container
    # is setup for using a "legacy" configuration for ssh)
    legacy_ssh_args = (
        "-o 'KexAlgorithms=diffie-hellman-group-exchange-sha1,diffie-hellman-group14-sha1,diffie-hellman-group1-sha1'"  # noqa: E501
        " -o 'HostKeyAlgorithms=+ssh-rsa,ssh-dss'"
        " -o 'PubkeyAcceptedKeyTypes=+ssh-rsa,ssh-dss'"
    )

    ansible_vars = {
        "ansible_port": connection_port,
        "ansible_ssh_common_args": legacy_ssh_args,
    }

    if credential is not None:
        ansible_dict = _credential_vars(credential)
        ansible_vars.update(ansible_dict)

    return ansible_vars


def construct_inventory(
    hosts,
    connection_port,
    concurrency_count,
    *,
    credential=None,
    exclude_hosts=None,
):
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


def expand_hostpattern(hostpattern):
    """Expand pattern into list of hosts.

    Takes a single host pattern and returns a list of hostnames.
    :param hostpattern: a single host pattern
    :returns: list of hostnames
    """
    # Can the given hostpattern be parsed as a host with an optional port
    # specification?

    try:

        (pattern, port) = parse_address(hostpattern, allow_ranges=True)
    except:  # noqa
        # not a recognizable host pattern
        pattern = hostpattern

    # Once we have separated the pattern, we expand it into list of one or
    # more hostnames, depending on whether it contains any [x:y] ranges.

    if detect_range(pattern):
        hostnames = expand_hostname_range(pattern)
    else:
        hostnames = [pattern]

    return hostnames


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
