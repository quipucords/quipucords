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

from ansible.inventory.expand_hosts import detect_range, expand_hostname_range
from ansible.parsing.utils.addresses import parse_address

from api.vault import decrypt_data_as_unicode

ANSIBLE_DEFAULT_ERR_MSG = 'An error occurred while executing the ' \
    'Ansible playbook. See logs for further details.'
ANSIBLE_FAILED_HOST_ERR_MSG = 'An error occurred while executing the ' \
    'Ansible playbook. A task failed to execute properly on a remote host.' \
    ' See logs for further details.'
ANSIBLE_UNREACHABLE_HOST_ERR_MSG = 'An error occurred while executing the ' \
    'Ansible playbook. Connection could not be made to the remote hosts.' \
    ' See logs for further details.'
ANSIBLE_PLAYBOOK_ERR_MSG = 'An error occurred while executing the ' \
    'Ansible playbook. An issue exists in the playbook being executed.' \
    ' See logs for further details.'
ANSIBLE_TIMEOUT_ERR_MSG = 'A timeout was reached while executing' \
    'the Ansible playbook.'


def _credential_vars(credential):
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


def _construct_playbook_error_msg(status):
    message = ANSIBLE_DEFAULT_ERR_MSG
    if status == 'timeout':
        message = ANSIBLE_TIMEOUT_ERR_MSG
    elif status == 'failed':
        message = ANSIBLE_FAILED_HOST_ERR_MSG
    elif status == 'unreachable':
        message = ANSIBLE_UNREACHABLE_HOST_ERR_MSG
    return message


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
