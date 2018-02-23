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
from fingerprinter.jboss_fuse import detect_jboss_fuse


class ProductFuseTest(TestCase):
    """Tests Product Fuse class."""

    def test_detect_jboss_fuse_present(self):
        """Test the detect_jboss_fuse method."""
        source = {'source_id': 1, 'source_type': 'network'}
        facts = {'eap_home_bin': {'opt/fuse/': ['jboss-fuse.jar']}}
        product = detect_jboss_fuse(source, facts)
        expected = {'name': 'JBoss Fuse',
                    'presence': 'present',
                    'metadata': {
                        'source_id': 1,
                        'source_name': None,
                        'source_type': 'network',
                        'raw_fact_key': 'eap_home_bin/karaf_home_bin_fuse'}}
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
                        'raw_fact_key': 'jboss_fuse_systemctl_unit_files/'
                                        'jboss_fuse_chkconfig'}}
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
                        'raw_fact_key': ''}}
        self.assertEqual(product, expected)
