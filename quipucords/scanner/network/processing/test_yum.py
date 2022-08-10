# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing of yum enabled repos fact."""


import unittest

from scanner.network.processing import yum
from scanner.network.processing.util_for_test import ansible_result


class TestProcessEnableYumRepolist(unittest.TestCase):
    """Test ProcessEnableYumRepolist."""

    def test_success_case(self):
        """Found yum_enabled_repolist."""
        input_data = (
            "You no longer have access to the repositories that "
            "provide these products. "
            "repo id"
            "repo name \n"
            "!jb-eap-7-for-rhel-7-server-rpms/7Server/x86_64 "
            "JBoss Enterprise Applicat    886\n"
            "!rhel-7-server-rpms/7Server/x86_64              "
            "Red Hat Enterprise Linux  17,664\n"
            "!rhel7-cdn-internal/7Server/x86_64              "
            "RHEL 7 - x86_64           17,471\n"
            "!rhel7-cdn-internal-extras/7Server/x86_64       "
            "RHEL 7 - x86_64              679\n"
            "!rhel7-cdn-internal-optional/7Server/x86_64     "
            "RHEL 7 - x86_64           12,921"
        )

        expected = [
            {
                "name": "JBoss Enterprise Applicat",
                "repo": "!jb-eap-7-for-rhel-7-server-rpms/7Server/x86_64",
            },
            {
                "name": "Red Hat Enterprise Linux",
                "repo": "!rhel-7-server-rpms/7Server/x86_64",
            },
            {
                "name": "RHEL 7 - x86_64",
                "repo": "!rhel7-cdn-internal/7Server/x86_64",
            },
            {
                "name": "RHEL 7 - x86_64",
                "repo": "!rhel7-cdn-internal-extras/7Server/x86_64",
            },
            {
                "name": "RHEL 7 - x86_64",
                "repo": "!rhel7-cdn-internal-optional/7Server/x86_64",
            },
        ]

        self.assertEqual(
            yum.ProcessEnableYumRepolist.process(ansible_result(input_data)), expected
        )

    def test_error_occurred(self):
        """Test output that should result in []."""
        input_data = "Loaded plugins: product-id, security, \
            subscription-manager\r\n"
        expected = []
        self.assertEqual(
            yum.ProcessEnableYumRepolist.process(ansible_result(input_data)), expected
        )

    def test_not_found(self):
        """Did not find yum_enabled_repolist."""
        self.assertEqual(yum.ProcessEnableYumRepolist.process(ansible_result("")), [])
