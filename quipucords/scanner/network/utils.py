#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Scanner used for host connection discovery."""

from collections import namedtuple

from ansible import constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory import Inventory
from ansible.inventory.expand_hosts import detect_range, expand_hostname_range
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.utils.addresses import parse_address
from ansible.playbook.play import Play
from ansible.vars import VariableManager

from api.vault import decrypt_data_as_unicode, write_to_yaml

from django.conf import settings


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


def write_inventory(inventory):
    """Write the inventory to a temporary file.

    :param inventory: A ansible inventory dictionary
    :returns: The path of the temporary failed
    """
    return write_to_yaml(inventory)


def create_ansible_objects(inventory_file, extra_vars, use_paramiko=None,
                           forks=50):
    """Create the default ansible objects needed to run a playbook.

    :param inventory_file: The path to the inventory file
    :param extra_vars: The dictionary containing
           the collection status of the optional products.
    :param use_paramiko: use paramiko instead of ssh for connection
    :param forks: number of forks to run with, default of 50
    :returns: tuple of (options, variable_manager, loader, inventory)
    """
    named_options = namedtuple('Options', ['connection', 'module_path',
                                           'forks', 'become', 'become_method',
                                           'become_user', 'check'])
    conn = 'ssh'
    # Change connection method from default ssh to paramiko if needed
    if use_paramiko:
        conn = 'paramiko'

    options = named_options(connection=conn,
                            module_path=C.DEFAULT_MODULE_PATH,
                            forks=forks, become=False,
                            become_method='sudo', become_user='root',
                            check=False)

    variable_manager = VariableManager()
    loader = DataLoader()
    loader.set_vault_password(settings.SECRET_KEY)

    # create inventory and extra vars and pass to var manager
    inventory = Inventory(loader=loader,
                          variable_manager=variable_manager,
                          host_list=inventory_file)
    variable_manager.extra_vars = extra_vars
    variable_manager.set_inventory(inventory)

    return options, variable_manager, loader, inventory


# pylint: disable=too-many-arguments
def run_playbook(inventory_file, callback, play,
                 extra_vars, use_paramiko=None, forks=50):
    """Run an ansible playbook.

    :param inventory_file: The path to the inventory file
    :param callback: The callback handler
    :param play: The playbook dictionary to run
    :param extra_vars: The dictionary containing
           the collection status of the optional products.
    :param use_paramiko: use paramiko instead of ssh for connection
    :param forks: number of forks to run with, default of 50
    :returns: The result of executing the play (return code)
    """
    options, variable_manager, loader, ansible_inventory = \
        create_ansible_objects(inventory_file, extra_vars, use_paramiko, forks)

    playbook = Play().load(play,
                           variable_manager=variable_manager,
                           loader=loader)

    task_manager = TaskQueueManager(
        inventory=ansible_inventory,
        variable_manager=variable_manager,
        loader=loader,
        options=options,
        passwords=None,
        stdout_callback=callback,
        run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS)

    return task_manager.run(playbook)


def _construct_error_msg(return_code):
    message = ANSIBLE_DEFAULT_ERR_MSG
    if return_code == TaskQueueManager.RUN_FAILED_HOSTS:
        message = ANSIBLE_FAILED_HOST_ERR_MSG
    elif return_code == TaskQueueManager.RUN_UNREACHABLE_HOSTS:
        message = ANSIBLE_UNREACHABLE_HOST_ERR_MSG
    elif return_code == TaskQueueManager.RUN_FAILED_BREAK_PLAY:
        message = ANSIBLE_PLAYBOOK_ERR_MSG
    return message


def expand_hostpattern(hostpattern):
    """Expand pattern into list of hosts.

    Takes a single host pattern and returns a list of hostnames.
    :param hostpattern: a single host pattern
    :returns: list of hostnames
    """
    # Can the given hostpattern be parsed as a host with an optional port
    # specification?

    try:
        # pylint: disable=unused-variable
        (pattern, port) = parse_address(hostpattern, allow_ranges=True)
    except:  # noqa pylint: disable=bare-except
        # not a recognizable host pattern
        pattern = hostpattern

    # Once we have separated the pattern, we expand it into list of one or
    # more hostnames, depending on whether it contains any [x:y] ranges.

    if detect_range(pattern):
        hostnames = expand_hostname_range(pattern)
    else:
        hostnames = [pattern]

    return hostnames
