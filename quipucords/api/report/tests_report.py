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
                        Credential)
from api.report.renderer import ReportCSVRenderer
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
            become_password=None,
            ssh_keyfile=None)
        self.net_source.credentials.add(self.net_cred)

        self.net_source.hosts = '["1.2.3.4"]'
        self.net_source.save()

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

    def test_get_group_count_report_list(self):
        """Get a group count report for all collections."""
        url = '/api/v1/reports/?group_count=os_release'

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

    def test_get_fact_collection_group_report_count(self):
        """Get a specific group count report."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        filters = {'fact_collection_id': 1, 'group_count': 'os_release'}
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.assertIsInstance(report, dict)
        self.assertEqual(report['report'][0]['count'], 2)
        self.assertEqual(report['report'][1]['count'], 1)

    def test_get_fact_collection_group_report(self):
        """Get a specific group count report."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        filters = {'fact_collection_id': 1}
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.assertIsInstance(report, dict)
        self.assertEqual(len(report['report'][0].keys()), 33)

    def test_get_fact_collection_filter_report(self):
        """Get a specific group count report with filter."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        filters = {'fact_collection_id': 1,
                   'os_name': True,
                   'os_release': 'true'}
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.assertIsInstance(report, dict)
        self.assertEqual(report['report'][0],
                         {'os_name': 'RHEL', 'os_release': 'RHEL 7.4'})

    def test_get_fact_collection_404(self):
        """Fail to get a report for missing collection."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        response = self.client.get(url, {'fact_collection_id': 2})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_group_count_400_invalid_field(self):
        """Fail to get report with invalid field for group_count."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        response = self.client.get(url, {'group_count': 'no_field'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_group_count_invalid_combo_400(self):
        """Fail to get report due to invalid filter combo."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        filters = {'group_count': 'os_release', 'os_name': 'true'}
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_group_count_invalid_combo2_400(self):
        """Fail to get report due to invalid filter combo."""
        url = '/api/v1/reports/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        filters = {'fact_collection_id': 1,
                   'group_count': 'os_release',
                   'os_name': 'true'}
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    ##############################################################
    # Test CSV Renderer
    ##############################################################
    def test_csv_renderer(self):
        """Test ReportCSVRenderer."""
        renderer = ReportCSVRenderer()
        # Test no FC id
        test_json = {}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        # Test doesn't exist
        test_json = {'id': 42}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])
        filters = {'fact_collection_id': 1}
        url = '/api/v1/reports/'
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()

        print(report)
        csv_result = renderer.render(report)

        # pylint: disable=line-too-long
        expected = 'Fact Collection\r\n1\r\n\r\n\r\nReport:\r\nbios_uuid,cpu_core_count,cpu_core_per_socket,cpu_count,cpu_hyperthreading,cpu_siblings,cpu_socket_count,infrastructure_type,ip_addresses,mac_addresses,name,os_name,os_release,os_version,subscription_manager_id,system_creation_date,virtualized_is_guest,virtualized_num_guests,virtualized_num_running_guests,virtualized_type,vm_cluster,vm_datacenter,vm_dns_name,vm_host,vm_host_cpu_cores,vm_host_cpu_threads,vm_host_socket_count,vm_memory_size,vm_state,vm_uuid\r\n,2,1,2,False,1,2,virtualized,,,1.2.3.4,RHEL,RHEL 7.4,7.4,,2017-07-18,True,1,1,vmware,,,,,,,,,,\r\n,2,1,2,False,1,2,virtualized,,,1.2.3.4,RHEL,RHEL 7.4,7.4,,2017-07-18,True,1,1,vmware,,,,,,,,,,\r\n,2,1,2,False,1,2,virtualized,,,1.2.3.4,RHEL,RHEL 7.5,7.5,,2017-07-18,True,1,1,vmware,,,,,,,,,,\r\n\r\n'  # noqa
        self.assertEqual(csv_result, expected)

    def test_csv_renderer_only_name(self):
        """Test ReportCSVRenderer name filter."""
        renderer = ReportCSVRenderer()
        # Test no FC id
        test_json = {}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        # Test doesn't exist
        test_json = {'id': 42}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])
        filters = {'fact_collection_id': 1, 'name': True}
        url = '/api/v1/reports/'
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()

        print(report)
        csv_result = renderer.render(report)

        # pylint: disable=line-too-long
        expected = 'Fact Collection\r\n1\r\n\r\n\r\nReport:\r\nname\r\n1.2.3.4\r\n1.2.3.4\r\n1.2.3.4\r\n\r\n'  # noqa
        self.assertEqual(csv_result, expected)
