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
"""Test the API application."""

from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework import status
from api.models import (Credential, Source, ScanJob,
                        ScanJobResults, Results, ResultKeyValue)
from api.serializers import (ResultKeyValueSerializer, ResultsSerializer)


class ScanJobResultsTest(TestCase):
    """Test the basic ScanJobResults infrastructure."""

    def setUp(self):
        """Create test setup."""
        self.cred = Credential.objects.create(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred_for_upload = self.cred.id

        self.source = Source(
            name='source1',
            ssh_port=22)
        self.source.save()
        self.source.credentials.add(self.cred)
        self.scanjob = ScanJob(source_id=self.source.id,
                               scan_type=ScanJob.DISCOVERY)
        self.scanjob.save()

    def test_get_results_not_present(self):
        """Get results on a specific ScanJob by primary key."""
        url = reverse('scanjob-detail', args=(self.scanjob.id,))
        url = url + 'results/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_validate_resultkeyvalue(self):
        """Check results key value constraints."""
        data = {'key': 'A' * 65,
                'value': 'value'}
        serializer = ResultKeyValueSerializer(data=data)
        serializer.is_valid()
        self.assertTrue(len(serializer.errors) > 0)

        data = {'key': 'key1',
                'value': 'A' * 2000}
        serializer = ResultKeyValueSerializer(data=data)
        serializer.is_valid()
        self.assertTrue(len(serializer.errors) > 0)

    def test_validate_results(self):
        """Check results constraints."""
        data = {'row': 'A' * 65}
        serializer = ResultsSerializer(data=data)
        serializer.is_valid()
        self.assertTrue(len(serializer.errors) > 0)

    def test_get_results_empty(self):
        """Get empty results on a specific ScanJob by primary key."""
        results = ScanJobResults(scan_job=self.scanjob,
                                 fact_collection_id=1)
        results.save()

        url = reverse('scanjob-detail', args=(self.scanjob.id,))
        url = url + 'results/'
        response = self.client.get(url)
        expected = {'fact_collection_id': 1, 'id': 1, 'scan_job': 1,
                    'results': []}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)

    def test_get_results(self):
        """Get results on a specific ScanJob by primary key."""
        results = ScanJobResults(scan_job=self.scanjob,
                                 fact_collection_id=1)
        results.save()

        row1 = Results(row='row1')
        row1.save()

        rkv1 = ResultKeyValue(key='key1', value='value1')
        rkv1.save()
        self.assertIsInstance(str(rkv1), str)
        row1.columns.add(rkv1)
        row1.save()
        results.results.add(row1)
        results.save()

        url = reverse('scanjob-detail', args=(self.scanjob.id,))
        url = url + 'results/'
        response = self.client.get(url)
        expected = {'fact_collection_id': 1, 'id': 1,
                    'results': [{'columns': [{'key': 'key1',
                                              'value': 'value1'}],
                                 'row': 'row1'}],
                    'scan_job': 1}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)
        self.assertIsInstance(str(rkv1), str)
        self.assertIsInstance(str(row1), str)
        self.assertIsInstance(str(results), str)
