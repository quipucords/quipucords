#
# Copyright (c) 2017-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Scanner used for host connection discovery."""

from functools import cache

import yaml
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.inventory import detect_range, expand_hostname_range
from django.conf import settings

from api.models import ScanJob
from api.vault import decrypt_data_as_unicode
from scanner.network.exceptions import NetworkCancelException, NetworkPauseException

# key is stop_type, value is manager_interrupt.value
STOP_STATES = {'cancel': ScanJob.JOB_TERMINATE_CANCEL,
               'pause': ScanJob.JOB_TERMINATE_PAUSE}


def check_manager_interrupt(interrupt_value):
    """Check if cancel & pause exception should be raised."""
    if interrupt_value == ScanJob.JOB_TERMINATE_CANCEL:
        raise NetworkCancelException()
    if interrupt_value == ScanJob.JOB_TERMINATE_PAUSE:
        raise NetworkPauseException()


def _credential_vars(credential):
    """Build a dictionary containing cred information."""
    ansible_dict = {}
    username = credential.get('username')
    password = credential.get('password')
    ssh_keyfile = credential.get('ssh_keyfile')
    become_method = credential.get('become_method')
    become_user = credential.get('become_user')
    become_password = credential.get('become_password')

    ansible_dict['ansible_user'] = username
    if password:
        ansible_dict['ansible_ssh_pass'] = \
            decrypt_data_as_unicode(password)
    if ssh_keyfile:
        ansible_dict['ansible_ssh_private_key_file'] = ssh_keyfile
    if become_password:
        ansible_dict['ansible_become_pass'] = \
            decrypt_data_as_unicode(become_password)
    if become_method:
        ansible_dict['ansible_become_method'] = become_method
    if become_user:
        ansible_dict['ansible_become_user'] = become_user
    return ansible_dict


def _construct_vars(connection_port, credential=None):
    """Get the Ansible host vars that implement a credential.

    :param connection_port: The connection port
    :param credential: The credential used for connections
    :returns: a dict that can be used as the host variables in an
        Ansible inventory.
    """
    ansible_vars = {'ansible_port': connection_port}

    if credential is not None:
        ansible_dict = _credential_vars(credential)
        ansible_vars.update(ansible_dict)

    return ansible_vars


def expand_hostpattern(hostpattern):
    """Expand pattern into list of hosts.

    Takes a single host pattern and returns a list of hostnames.
    :param hostpattern: a single host pattern
    :returns: list of hostnames
    """
    # Can the given hostpattern be parsed as a host with an optional port
    # specification?
    # pylint: disable=bare-except
    try:
        # pylint: disable=unused-variable
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
def results_template():
    """Results template for fact collection on network scans."""
    return {fact_name: None for fact_name in sorted(collect_all_fact_names())}
