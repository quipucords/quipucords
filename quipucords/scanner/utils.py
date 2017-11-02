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
"""Scanner used for host connection discovery"""

from collections import namedtuple
import pexpect
from django.conf import settings
from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.splitter import parse_kv
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from api.vault import decrypt_data_as_unicode, write_to_yaml
from scanner.callback import ResultCallback


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
    username = credential['username']
    password = credential['password']
    ssh_keyfile = credential['ssh_keyfile']
    sudo_password = credential['sudo_password']

    ansible_dict['ansible_user'] = username
    if password:
        ansible_dict['ansible_ssh_pass'] = \
            decrypt_data_as_unicode(password)
    if ssh_keyfile:
        ansible_dict['ansible_ssh_private_key_file'] = ssh_keyfile
    if sudo_password:
        ansible_dict['ansible_become_pass'] = \
            decrypt_data_as_unicode(sudo_password)
    return ansible_dict


def _construct_vars(connection_port, credential=None):
    """Get the Ansible host vars that implement an auth.

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


def construct_connect_inventory(hosts, credential, connection_port):
    """Create a dictionary inventory for Ansible to execute with.

    :param hosts: The collection of hosts to test connections
    :param credential: The credential used for connections
    :param connection_port: The connection port
    :returns: A dictionary of the ansible invetory
    """
    inventory = None
    hosts_dict = {}

    for host in hosts:
        hosts_dict[host] = None

    vars_dict = _construct_vars(connection_port, credential)

    inventory = {'all': {'hosts': hosts_dict, 'vars': vars_dict}}
    return inventory


def construct_scan_inventory(hosts,
                             connection_port,
                             concurrency_count):
    """Create a dictionary inventory for Ansible to execute with.

    :param hosts: The collection of hosts/credential tuples
    :param connection_port: The connection port
    :returns: A dictionary of the ansible invetory
    """

    concurreny_groups = list(
        [hosts[i:i + concurrency_count] for i in range(0,
                                                       len(hosts),
                                                       concurrency_count)])

    # inventory = {'all': {'hosts': hosts_dict, 'vars': vars_dict}}

    vars_dict = _construct_vars(connection_port)
    children = {}
    inventory = {'all': {'children': children, 'vars': vars_dict}}
    i = 0
    group_names = []
    for concurreny_group in concurreny_groups:
        hosts_dict = {}
        for host in concurreny_group:
            host_vars = _credential_vars(host[1])
            host_vars['ansible_host'] = host[0]
            hosts_dict[host[0]] = host_vars

        group_name = 'group_{}'.format(i)
        i += 1
        group_names.append(group_name)
        children[group_name] = {'hosts': hosts_dict}

    return group_names, inventory


def write_inventory(inventory):
    """Write the inventory to a temporary file

    :param inventory: A ansible inventory dictionary
    :returns: The path of the temporary failed
    """
    return write_to_yaml(inventory)


def create_ansible_objects(inventory_file, forks=50):
    """ Created the default ansible objects needed to run a playbook.

    :param inventory_file: The path to the inventory file
    :param forks: number of forks to run with, default of 50
    :returns: tuple of (options, variable_manager, loader, inventory)
    """
    named_options = namedtuple('Options', ['connection', 'module_path',
                                           'forks', 'become', 'become_method',
                                           'become_user', 'check'])
    options = named_options(connection='ssh',
                            module_path=C.DEFAULT_MODULE_PATH,
                            forks=forks, become=True,
                            become_method='sudo', become_user='root',
                            check=False)

    variable_manager = VariableManager()
    loader = DataLoader()
    loader.set_vault_password(settings.SECRET_KEY)

    # create inventory and pass to var manager
    inventory = Inventory(loader=loader,
                          variable_manager=variable_manager,
                          host_list=inventory_file)
    variable_manager.set_inventory(inventory)

    return options, variable_manager, loader, inventory


def run_playbook(inventory_file, callback, play, forks=50):
    """Run an ansible playbook

    :param inventory_file: The path to the inventory file
    :param callback: The callback handler
    :param play: The playbook dictionary to run
    :param forks: number of forks to run with, default of 50
    :returns: The result of executing the play (return code)
    """
    options, variable_manager, loader, ansible_inventory = \
        create_ansible_objects(inventory_file, forks)

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


def _process_connect_callback(callback, credential):
    """Processes the callback information from a scan to create the success
    and failed lists.

    :param callback: The callback handler
    :param credential: The credential used for connections
    :returns: list of connected hosts credential tuples and
              list of host that failed connection
    """
    success = []
    failed = []
    if isinstance(callback, ResultCallback):
        for connection_result in callback.results:
            if 'host' in connection_result:
                host = connection_result['host']
                if 'result' in connection_result:
                    task_result = connection_result['result']
                    if 'rc' in task_result and task_result['rc'] is 0:
                        success.append((host, credential))
                    else:
                        failed.append(host)
                else:
                    failed.append(host)

    return success, failed


def _construct_error(return_code):
    message = ANSIBLE_DEFAULT_ERR_MSG
    if return_code == TaskQueueManager.RUN_FAILED_HOSTS:
        message = ANSIBLE_FAILED_HOST_ERR_MSG
    elif return_code == TaskQueueManager.RUN_UNREACHABLE_HOSTS:
        message = ANSIBLE_UNREACHABLE_HOST_ERR_MSG
    elif return_code == TaskQueueManager.RUN_FAILED_BREAK_PLAY:
        message = ANSIBLE_PLAYBOOK_ERR_MSG
    return AnsibleError(message=message)


def _handle_ssh_passphrase(credential):
    """Attempt to setup loggin via passphrase if necessary.

    :param credential: The credential used for connections
    """
    if (credential['ssh_keyfile'] is not None and
            credential['ssh_passphrase'] is not None):
        keyfile = credential['ssh_keyfile']
        passphrase = \
            decrypt_data_as_unicode(credential['ssh_passphrase'])
        cmd_string = 'ssh-add {}'.format(keyfile)

        try:
            child = pexpect.spawn(cmd_string, timeout=12)
            phrase = [pexpect.EOF, 'Enter passphrase for .*:']
            i = child.expect(phrase)
            child.sendline(passphrase)
            while i:
                i = child.expect(phrase)
        except pexpect.exceptions.TIMEOUT:
            pass


def connect(hosts, credential, connection_port, forks=50):
    """Attempt to connect to hosts using the given credential.

    :param hosts: The collection of hosts to test connections
    :param credential: The credential used for connections
    :param connection_port: The connection port
    :param forks: number of forks to run with, default of 50
    :returns: list of connected hosts credential tuples and
              list of host that failed connection
    """
    success = []
    failed = []
    inventory = construct_connect_inventory(hosts, credential, connection_port)
    inventory_file = write_inventory(inventory)
    callback = ResultCallback()

    playbook = {'name': 'discovery play',
                'hosts': 'all',
                'gather_facts': 'no',
                'tasks': [{'action': {'module': 'raw',
                                      'args': parse_kv('echo "Hello"')}}]}

    _handle_ssh_passphrase(credential)
    result = run_playbook(inventory_file, callback, playbook, forks=forks)
    if (result != TaskQueueManager.RUN_OK and
            result != TaskQueueManager.RUN_UNREACHABLE_HOSTS):
        raise _construct_error(result)

    success, failed = _process_connect_callback(callback, credential)

    return success, failed
