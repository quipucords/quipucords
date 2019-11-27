# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Unit tests for processing the user_data role."""

import unittest

from scanner.network.processing import user_data
from scanner.network.processing.util_for_test import ansible_result


class TestProcessUserInfo(unittest.TestCase):
    """Test ProcessUserInfo."""

    def test_success_case(self):
        """Processed result of user_info."""
        dependencies = {'internal_user_info':
                        ansible_result('a\nb\nc')}
        self.assertEqual(
            user_data.ProcessUserInfo.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            ['a', 'b', 'c'])
        # stdout_lines looks like ['', 'b']
        dependencies['internal_user_info'] = \
            ansible_result('\nb\n')
        self.assertEqual(
            user_data.ProcessUserInfo.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            ['b'])
        dependencies['internal_user_info'] = ansible_result(
            'Failed', 1)
        self.assertEqual(
            user_data.ProcessUserInfo.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '')

    def test_not_found(self):
        """No result for the user_info fact."""
        dependencies = {}
        self.assertEqual(
            user_data.ProcessUserInfo.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '')


class TestProcessUserLoginHistory(unittest.TestCase):
    """Test ProcessUserLoginHistory."""

    def test_success_case(self):
        """Found user login history fact."""
        dependencies = {'internal_user_login_history':
                        ansible_result('a\nb\nc')}
        self.assertEqual(
            user_data.ProcessUserLoginHistory.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            ['a', 'b', 'c'])
        # stdout_lines looks like ['', 'b']
        dependencies['internal_user_login_history'] = \
            ansible_result('\nb\n')
        self.assertEqual(
            user_data.ProcessUserLoginHistory.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            ['b'])
        dependencies['internal_user_login_history'] = ansible_result(
            'Failed', 1)
        self.assertEqual(
            user_data.ProcessUserLoginHistory.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '')

    def test_not_found(self):
        """Did not find user login history."""
        dependencies = {}
        self.assertEqual(
            user_data.ProcessUserLoginHistory.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '')


class TestProcessUserDeleteHistory(unittest.TestCase):
    """Test ProcessUserDeleteHistory."""

    def test_success_case(self):
        """Found user delete history fact."""
        dependencies = {'internal_user_delete_history':
                        ansible_result('a\nb\nc')}
        self.assertEqual(
            user_data.ProcessUserDeleteHistory.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            ['a', 'b', 'c'])
        # stdout_lines looks like ['', 'b']
        dependencies['internal_user_delete_history'] = \
            ansible_result('\nb\n')
        self.assertEqual(
            user_data.ProcessUserDeleteHistory.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            ['b'])
        dependencies['internal_user_delete_history'] = ansible_result(
            'Failed', 1)
        self.assertEqual(
            user_data.ProcessUserDeleteHistory.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '')

    def test_not_found(self):
        """Did not find user delete history."""
        dependencies = {}
        self.assertEqual(
            user_data.ProcessUserDeleteHistory.process(
                'QPC_FORCE_POST_PROCESS', dependencies),
            '')
