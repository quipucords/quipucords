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
from django.conf import settings
from ansible import constants as C
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.splitter import parse_kv
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from api.vault import decrypt_data_as_unicode, write_to_yaml
from scanner.callback import ResultCallback


def _construct_vars(credential, connection_port):
    """Get the Ansible host vars that implement an auth.

    :param credential: The credential used for connections
    :param connection_port: The connection port
    :returns: a dict that can be used as the host variables in an
        Ansible inventory.
    """

    username = credential['username']
    password = credential['password']
    ssh_keyfile = credential['ssh_keyfile']
    sudo_password = credential['sudo_password']

    ansible_vars = {'ansible_port': connection_port}

    ansible_vars['ansible_user'] = username
    if password:
        ansible_vars['ansible_ssh_pass'] = decrypt_data_as_unicode(password)
    if ssh_keyfile:
        ansible_vars['ansible_ssh_private_key_file'] = ssh_keyfile
    if sudo_password:
        ansible_vars['ansible_become_pass'] = \
            decrypt_data_as_unicode(sudo_password)

    return ansible_vars


def construct_inventory(hosts, credential, connection_port):
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

    vars_dict = _construct_vars(credential, connection_port)

    inventory = {'all': {'hosts': hosts_dict, 'vars': vars_dict}}
    return inventory


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
                            forks=forks, become=None,
                            become_method=None, become_user=None, check=False)

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


def connect(hosts, credential, connection_port):
    """Attempt to connect to hosts using the given credential.

    :param hosts: The collection of hosts to test connections
    :param credential: The credential used for connections
    :param connection_port: The connection port
    :returns: list of connected hosts credential tuples and
              list of host that failed connection
    """
    success = []
    failed = []
    inventory = construct_inventory(hosts, credential, connection_port)
    inventory_file = write_inventory(inventory)

    # Instantiate our ResultCallback for handling results as they come in
    callback = ResultCallback()

    playbook = {'name': 'discovery play',
                'hosts': 'all',
                'gather_facts': 'no',
                'tasks': [{'action': {'module': 'raw',
                                      'args': parse_kv('echo "Hello"')}}]}

    result = run_playbook(inventory_file, callback, playbook)
    if result != TaskQueueManager.RUN_OK:
        return success, hosts

    success, failed = _process_connect_callback(callback, credential)

    return success, failed
