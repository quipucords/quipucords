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
"""Test the report API."""

import json
import uuid
from django.test import TestCase
from django.core.urlresolvers import reverse
from api.models import (Source,
                        Credential,
                        HostRange)
from rest_framework import status


class SystemReportTest(TestCase):
    """Tests against the System reports function."""

    # pylint: disable= no-self-use, invalid-name
    def setUp(self):
        """Create test case setup."""
        self.net_source = Source.objects.create(
            name='test_source', source_type=Source.NETWORK_SOURCE_TYPE)

        self.net_cred = Credential.objects.create(
            name='net_cred1',
            cred_type=Credential.NETWORK_CRED_TYPE,
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.net_source.credentials.add(self.net_cred)

        host_range = HostRange(source=self.net_source, host_range='1.2.3.4')
        host_range.save()

        self.net_source.hosts.add(host_range)

    def create_fact_collection(self, data):
        """Call the create endpoint."""
        url = reverse('facts-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_fact_collection_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_fact_collection(data)
        if response.status_code != status.HTTP_201_CREATED:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def generate_fingerprints(self,
                              os_name='RHEL',
                              os_versions=None):
        """Create a FactCollection for test."""
        facts = []
        fc_json = {'sources': [{'source_id': self.net_source.id,
                                'source_type': self.net_source.source_type,
                                'facts': facts}]}

        if os_versions is None:
            os_versions = ['7.3', '7.4']

        for version in os_versions:
            release = '{} {}'.format(os_name, version)
            fact_json = {
                'connection_host': '1.2.3.4',
                'connection_port': 22,
                'connection_uuid': str(
                    uuid.uuid4()),
                'cpu_count': 2,
                'cpu_core_per_socket': 1,
                'cpu_siblings': 1,
                'cpu_hyperthreading': False,
                'cpu_socket_count': 2,
                'cpu_core_count': 2,
                'date_anaconda_log': '2017-07-18',
                'date_yum_history': '2017-07-18',
                'etc_release_name': os_name,
                'etc_release_version': version,
                'etc_release_release': release,
                'virt_virt': 'virt-guest',
                'virt_type': 'vmware',
                'virt_num_guests': 1,
                'virt_num_running_guests': 1,
                'virt_what_type': 'vt'
            }
            facts.append(fact_json)
        fact_collection = self.create_fact_collection_expect_201(fc_json)
        return fact_collection

    def test_get_report_list(self):
        """Create fact collection object via API."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via fact collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report_list = response.json()
        self.assertIsInstance(report_list, list)
        self.assertEqual(len(report_list), 1)
        self.assertEqual(report_list[0]['report'][0]['count'], 2)
        self.assertEqual(report_list[0]['report'][1]['count'], 1)

    def test_get_fact_collection_report(self):
        """Create fact collection object via API."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        response = self.client.get(url, {'fact_collection_id': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.assertIsInstance(report, dict)
        self.assertEqual(report['report'][0]['count'], 2)
        self.assertEqual(report['report'][1]['count'], 1)

    def test_get_fact_collection_404(self):
        """Create fact collection object via API."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        response = self.client.get(url, {'fact_collection_id': 2})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
