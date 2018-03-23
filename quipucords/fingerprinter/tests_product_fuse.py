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

"""Test the product fuse."""

from django.test import TestCase
from fingerprinter.jboss_fuse import (detect_jboss_fuse,
                                      get_versions)


class ProductFuseTest(TestCase):
    """Tests Product Fuse class."""

    def test_detect_jboss_fuse_present(self):
        """Test the detect_jboss_fuse method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'eap_home_bin': {'opt/fuse/': ['jboss-fuse.jar']},
                 'jboss_activemq_ver': ['redhat-630187']}
        product = detect_jboss_fuse(source, facts)
        expected = {'name': 'JBoss Fuse',
                    'presence': 'present',
                    'version': ['Fuse-6.3.0'],
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'network',
                        'raw_fact_key': 'eap_home_bin/jboss_activemq_ver'}}
        self.assertEqual(product, expected)

    # pylint: disable=C0103
    def test_detect_jboss_fuse_potential_init(self):
        """Test the detect_jboss_fuse method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'jboss_fuse_systemctl_unit_files': ['jboss_fuse_init']}
        product = detect_jboss_fuse(source, facts)
        expected = {'name': 'JBoss Fuse',
                    'presence': 'potential',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'network',
                        'raw_fact_key': 'jboss_fuse_systemctl_unit_files'}}
        self.assertEqual(product, expected)

    def test_detect_jboss_fuse_potential_sub(self):
        """Test the detect_jboss_fuse method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'subman_consumed': [{'name': 'JBoss Fuse Sub'}]}
        product = detect_jboss_fuse(source, facts)
        expected = {'name': 'JBoss Fuse',
                    'presence': 'potential',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'network',
                        'raw_fact_key': 'subman_consumed'}}
        self.assertEqual(product, expected)

    def test_detect_jboss_fuse_potential_ent(self):
        """Test the detect_jboss_fuse method."""
        source = {'source_id': 1, 'source_type': 'satellite'}
        facts = {'entitlements': [{'name': 'JBoss Fuse Sub'}]}
        product = detect_jboss_fuse(source, facts)
        expected = {'name': 'JBoss Fuse',
                    'presence': 'potential',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'satellite',
                        'raw_fact_key': 'entitlements'}}
        self.assertEqual(product, expected)

    def test_detect_jboss_fuse_absent(self):
        """Test the detect_jboss_fuse method."""
        source = {'source_id': 1, 'source_type': 'satellite'}
        facts = {'entitlements': [{'name': 'Satellite Sub'}]}
        product = detect_jboss_fuse(source, facts)
        expected = {'name': 'JBoss Fuse',
                    'presence': 'absent',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'satellite',
                        'raw_fact_key': None}}
        self.assertEqual(product, expected)

    def test_detect_fuse_present(self):
        """Test the detect_jboss_fuse method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'eap_home_bin': {'opt/fuse/': ['jboss-fuse.jar']},
                 'fuse_camel_version': ['redhat-630187'],
                 'jboss_fuse_on_eap_activemq_ver': [{'homedir': '/foo/bin',
                                                     'version':
                                                         ['redhat-630187']}]}
        product = detect_jboss_fuse(source, facts)
        expected = {'name': 'JBoss Fuse',
                    'presence': 'present',
                    'version': ['Fuse-6.3.0'],
                    'metadata':
                        {'source_id': 1,
                         'source_name': None,
                         'source_type': 'network',
                         'raw_fact_key':
                             'eap_home_bin/fuse_camel_version/'
                             'jboss_fuse_on_eap_activemq_ver'}}
        self.assertEqual(product, expected)

    def test_get_versions(self):
        """Test the get_versions method."""
        eap_camel = [{'homedir': '/foo/bin',
                      'version': ['redhat-620133']}]
        eap_cxf = [{'homedir': '/foo/bin',
                    'version': ['redhat-630187']}]
        eap_activemq = []
        versions = get_versions(eap_camel + eap_cxf + eap_activemq)
        expected = ['redhat-620133', 'redhat-630187']
        self.assertEqual(versions, expected)
