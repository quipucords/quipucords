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

"""Test the product brms."""

from django.test import TestCase
from fingerprinter.jboss_brms import detect_jboss_brms


class ProductBRMSTest(TestCase):
    """Tests Product BRMS class."""

    def test_detect_jboss_brms_present(self):
        """Test the detect_jboss_brms method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'jboss_brms_manifest_mf':
                 {('/opt/brms', '6.4.0.Final-redhat-3')},
                 'jboss_brms_kie_api_ver':
                 {('/opt/brms', '6.4.0.Final-redhat-3')}}
        product = detect_jboss_brms(source, facts)
        expected = {'name': 'JBoss BRMS',
                    'presence': 'present',
                    'version': ['BRMS 6.3.0'],
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'network',
                        'raw_fact_key': 'jboss_brms_kie_api_ver/'
                                        'jboss_brms_manifest_mf'}}
        self.assertEqual(product, expected)

    # pylint: disable=C0103
    def test_detect_jboss_brms_potential_sub(self):
        """Test the detect_jboss_brms method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'subman_consumed': [{'name': 'JBoss BRMS Sub'}]}
        product = detect_jboss_brms(source, facts)
        expected = {'name': 'JBoss BRMS',
                    'presence': 'potential',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'network',
                        'raw_fact_key': 'subman_consumed'}}
        self.assertEqual(product, expected)

    def test_detect_jboss_brms_potential_ent(self):
        """Test the detect_jboss_brms method."""
        source = {'source_id': 1, 'source_type': 'satellite'}
        facts = {'entitlements': [{'name': 'JBoss BRMS Sub'}]}
        product = detect_jboss_brms(source, facts)
        expected = {'name': 'JBoss BRMS',
                    'presence': 'potential',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'satellite',
                        'raw_fact_key': 'entitlements'}}
        self.assertEqual(product, expected)

    def test_detect_jboss_brms_absent(self):
        """Test the detect_jboss_brms method."""
        source = {'source_id': 1, 'source_type': 'satellite'}
        facts = {'entitlements': [{'name': 'Satellite Sub'}]}
        product = detect_jboss_brms(source, facts)
        expected = {'name': 'JBoss BRMS',
                    'presence': 'absent',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'satellite',
                        'raw_fact_key': None}}
        self.assertEqual(product, expected)
