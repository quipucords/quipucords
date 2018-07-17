#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Test the product JBoss Web Server."""

from unittest.mock import patch

from api.models import ServerInformation

from django.test import TestCase

from fingerprinter.jboss_web_server import (detect_jboss_ws,
                                            get_version, has_jboss_eula_file,
                                            installed_with_rpm)


class ProductFuseTest(TestCase):
    """Tests Product Fuse class."""

    def setUp(self):
        """Create test case setup."""
        self.server_id = ServerInformation.create_or_retreive_server_id()

    def test_get_version(self):
        """Test the get_version method."""
        rawjson = {'results': [{'stdout_lines': ['JWS_3.0.3']}]}
        versions = get_version(rawjson)
        expected = ['JWS 3.0.3']

        self.assertEqual(versions, expected)

    def test_installed_with_rpm(self):
        """Test the installed_with_rpm method."""
        expected = ['Red Hat JBoss Web Server']
        self.assertEqual(installed_with_rpm('not installed'), False)
        self.assertEqual(installed_with_rpm(expected), True)

    def test_has_jboss_eula_file(self):
        """Test the has_jboss_eula_file method."""
        ls_err = 'No such file or directory'
        self.assertEqual(has_jboss_eula_file('JBossEula.txt'), True)
        self.assertEqual(has_jboss_eula_file(ls_err), False)

    # pylint: disable=unused-argument
    @patch('fingerprinter.jboss_web_server.get_version',
           return_value=['version1'])
    @patch('fingerprinter.jboss_web_server.installed_with_rpm',
           return_value=True)
    def test_detect_ws_present(self, mock_version, mock_rpm):
        """Test the detect_jboss_ws method."""
        source = {'server_id': self.server_id,
                  'source_name': 'source1', 'source_type': 'network'}
        facts = {}
        product = detect_jboss_ws(source, facts)
        expected = {'name': 'JBoss WS',
                    'presence': 'present',
                    'version': ['version1'],
                    'metadata':
                        {'server_id': self.server_id,
                         'source_name': 'source1',
                         'source_type': 'network'}}
        self.assertEqual(product, expected)

    # pylint: disable=unused-argument
    @patch('fingerprinter.jboss_web_server.get_version',
           return_value=['version1'])
    @patch('fingerprinter.jboss_web_server.installed_with_rpm',
           return_value=False)
    @patch('fingerprinter.jboss_web_server.has_jboss_eula_file',
           return_value=True)
    def test_detect_ws_potential(self, mock_version, mock_rpm, mock_eula):
        """Test the detect_jboss_ws method."""
        # Test where tomcat is part of red hat product
        source = {'server_id': self.server_id,
                  'source_name': 'source1', 'source_type': 'network'}
        facts = {'tomcat_is_part_of_redhat_product': True}
        product = detect_jboss_ws(source, facts)
        expected = {'name': 'JBoss WS',
                    'presence': 'potential',
                    'version': ['version1'],
                    'metadata':
                        {'server_id': self.server_id,
                         'source_name': 'source1',
                         'source_type': 'network'}}
        self.assertEqual(product, expected)

        # Test where JWS_HOME contains jboss eula file
        facts = {'tomcat_is_part_of_redhat_product': False}
        product = detect_jboss_ws(source, facts)
        self.assertEqual(product, expected)

    # pylint: disable=unused-argument
    @patch('fingerprinter.jboss_web_server.get_version',
           return_value=[])
    @patch('fingerprinter.jboss_web_server.installed_with_rpm',
           return_value=False)
    @patch('fingerprinter.jboss_web_server.has_jboss_eula_file',
           return_value=False)
    def test_detect_ws_absent(self, mock_version, mock_rpm, mock_eula):
        """Test the detect_jboss_ws method."""
        # Test where tomcat is part of red hat product
        source = {'server_id': self.server_id,
                  'source_name': 'source1', 'source_type': 'network'}
        facts = {'tomcat_is_part_of_redhat_product': False}
        product = detect_jboss_ws(source, facts)
        expected = {'name': 'JBoss WS',
                    'presence': 'absent',
                    'version': [],
                    'metadata':
                        {'server_id': self.server_id,
                         'source_name': 'source1',
                         'source_type': 'network'}}
        self.assertEqual(product, expected)
