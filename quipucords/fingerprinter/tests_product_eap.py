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

"""Test the product eap."""

from django.test import TestCase
from fingerprinter.jboss_eap import detect_jboss_eap


class ProductEAPTest(TestCase):
    """Tests Product EAP class."""

    def test_detect_jboss_eap_present(self):
        """Test the detect_jboss_eap method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'eap_home_ls': {'opt/eap6/': ['jboss-modules.jar']}}
        product = detect_jboss_eap(source, facts)
        expected = {'name': 'JBoss EAP',
                    'presence': 'present',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'network',
                        'raw_fact_key': 'jboss_eap_running_paths'
                                        '/jboss_eap_packages'
                                        '/jboss_eap_locate_jboss_modules_jar'
                                        '/eap_home_ls'}}
        self.assertEqual(product, expected)

    # pylint: disable=C0103
    def test_detect_jboss_eap_potential_common(self):
        """Test the detect_jboss_eap method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'jboss_eap_common_files': ['jboss-modules.jar']}
        product = detect_jboss_eap(source, facts)
        expected = {'name': 'JBoss EAP',
                    'presence': 'potential',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'network',
                        'raw_fact_key': 'jboss_eap_id_jboss/'
                                        'jboss_eap_common_files/'
                                        'jboss_eap_processes/'
                                        'jboss_eap_systemctl_unit_files/'
                                        'jboss_eap_chkconfig'}}
        self.assertEqual(product, expected)

    def test_detect_jboss_eap_potential_sub(self):
        """Test the detect_jboss_eap method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'subman_consumed': [{'name': 'JBoss EAP Sub'}]}
        product = detect_jboss_eap(source, facts)
        expected = {'name': 'JBoss EAP',
                    'presence': 'potential',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'network',
                        'raw_fact_key': 'subman_consumed'}}
        self.assertEqual(product, expected)

    def test_detect_jboss_eap_potential_ent(self):
        """Test the detect_jboss_eap method."""
        source = {'source_id': 1, 'source_type': 'satellite'}
        facts = {'entitlements': [{'name': 'JBoss EAP Sub'}]}
        product = detect_jboss_eap(source, facts)
        expected = {'name': 'JBoss EAP',
                    'presence': 'potential',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'satellite',
                        'raw_fact_key': 'entitlements'}}
        self.assertEqual(product, expected)

    def test_detect_jboss_eap_absent(self):
        """Test the detect_jboss_eap method."""
        source = {'source_id': 1, 'source_type': 'satellite'}
        facts = {'entitlements': [{'name': 'Satellite Sub'}]}
        product = detect_jboss_eap(source, facts)
        expected = {'name': 'JBoss EAP',
                    'presence': 'absent',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'satellite',
                        'raw_fact_key': ''}}
        self.assertEqual(product, expected)
