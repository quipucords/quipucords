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
"""Test the fact API"""

import uuid
from django.test import TestCase
from api.fact_model import FactCollection, Fact
from api.report_model import SystemFingerprint
from rest_framework import status


class SystemReportTest(TestCase):
    """ Tests against the System reports function."""
    # pylint: disable= no-self-use

    def create_fact_collection(self,
                               os_name='RHEL',
                               os_versions=None):
        """Helper to create a FactCollection for test."""

        fact_collection = FactCollection.objects.create()

        if os_versions is None:
            os_versions = ['7.3', '7.4']

        fact_collection.facts = []

        for version in os_versions:
            release = '{} {}'.format(os_name, version)
            fact = Fact.objects.create(etc_release_name=os_name,
                                       etc_release_version=version,
                                       etc_release_release=release,
                                       connection_uuid=str(uuid.uuid4()))
            fact_collection.facts.add(fact)

        fact_collection.save()
        return fact_collection

    def create_fingerprints(self, fact_collection):
        """Helper to create a SystemFingerprint for test."""

        fingerprints = []
        for fact in fact_collection.facts.all():
            fingerprint = SystemFingerprint \
                .objects.create(fact_collection=fact_collection,
                                os_name=fact.etc_release_name,
                                os_release=fact.etc_release_release,
                                os_version=fact.etc_release_version)
            fingerprints.append(fingerprint)

        return fingerprints

    def test_fc_creation(self):
        """ Test model creation not via API."""
        fingerprints = self.create_fingerprints(self.create_fact_collection())
        for fingerprint in fingerprints:
            self.assertTrue(isinstance(fingerprint, SystemFingerprint))
            self.assertIsInstance(str(fingerprint), str)

    def test_get_report_list(self):
        """ Create fact collection object via API."""

        url = '/api/v1/reports/'

        # Create a system fingerprint
        self.create_fingerprints(self.create_fact_collection(
            os_versions=['7.4', '7.4', '7.5']))

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report_list = response.json()
        self.assertIsInstance(report_list, list)
        self.assertEqual(len(report_list), 1)
        self.assertEqual(report_list[0]['report'][0]['count'], 2)
        self.assertEqual(report_list[0]['report'][1]['count'], 1)

    def test_get_fact_collection_report(self):
        """ Create fact collection object via API."""

        url = '/api/v1/reports/'

        # Create a system fingerprint
        self.create_fingerprints(self.create_fact_collection(
            os_versions=['7.4', '7.4', '7.5']))

        # Query API
        response = self.client.get(url, {'fact_collection_id': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.assertIsInstance(report, dict)
        self.assertEqual(report['report'][0]['count'], 2)
        self.assertEqual(report['report'][1]['count'], 1)

    def test_get_fact_collection_404(self):
        """ Create fact collection object via API."""

        url = '/api/v1/reports/'

        # Create a system fingerprint
        self.create_fingerprints(self.create_fact_collection(
            os_versions=['7.4', '7.4', '7.5']))

        # Query API
        response = self.client.get(url, {'fact_collection_id': 2})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
