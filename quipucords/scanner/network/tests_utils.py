# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test the network scanner utility functions."""


import unittest
from unittest import mock
from ansible.executor.task_queue_manager import TaskQueueManager
from scanner.network import utils


class TestConstructVars(unittest.TestCase):
    """Test _construct_vars."""

    # pylint: disable=protected-access
    @mock.patch('scanner.network.utils.decrypt_data_as_unicode')
    def test_construct_vars(self, decrypt_data):
        """Test constructing ansible vars dictionary."""
        decrypt_data.side_effect = lambda x: x
        vars_dict = utils._construct_vars(22, {
            'name': 'cred1',
            'username': 'username',
            'password': 'password',
            'sudo_password': 'sudo',
            'ssh_keyfile': 'keyfile'})
        expected = {'ansible_become_pass': 'sudo', 'ansible_port': 22,
                    'ansible_ssh_pass': 'password',
                    'ansible_ssh_private_key_file': 'keyfile',
                    'ansible_user': 'username'}
        self.assertEqual(vars_dict, expected)


class TestConstructError(unittest.TestCase):
    """Test _construct_error."""

    # pylint: disable=protected-access
    def test_construct_error(self):
        """Test the creation of different errors."""
        error = utils._construct_error(TaskQueueManager.RUN_FAILED_HOSTS)
        self.assertEqual(error.message, utils.ANSIBLE_FAILED_HOST_ERR_MSG)
        error = utils._construct_error(TaskQueueManager.RUN_UNREACHABLE_HOSTS)
        self.assertEqual(error.message, utils.ANSIBLE_UNREACHABLE_HOST_ERR_MSG)
        error = utils._construct_error(TaskQueueManager.RUN_FAILED_BREAK_PLAY)
        self.assertEqual(error.message, utils.ANSIBLE_PLAYBOOK_ERR_MSG)
