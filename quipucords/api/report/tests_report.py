#
# Copyright (c) 2017-2018 Red Hat, Inc.
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
import copy
from django.test import TestCase
from django.core.urlresolvers import reverse
from api.models import (Source,
                        Credential,
                        FactCollection)
from api.report.renderer import ReportCSVRenderer, FactCollectionCSVRenderer
from rest_framework import status


class DetailReportTest(TestCase):
    """Tests against the Detail reports function."""

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

    def create(self, data):
        """Call the create endpoint."""
        url = reverse('facts-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create(data)
        if response.status_code != status.HTTP_201_CREATED:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def retrieve_expect_200(self, identifier):
        """Create a source, return the response as a dict."""
        url = '/api/v1/reports/' + str(identifier) + '/details/'
        response = self.client.get(url)

        if response.status_code != status.HTTP_200_OK:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    ##############################################################
    # Test details endpoint
    ##############################################################
    def test_details(self):
        """Get details for a report via API."""
        request_json = {'sources':
                        [{'source_id': self.net_source.id,
                          'source_type': self.net_source.source_type,
                          'facts': [{'key': 'value'}]}]}

        response_json = self.create_expect_201(
            request_json)
        identifier = response_json['id']
        response_json = self.retrieve_expect_200(identifier)
        self.assertEqual(response_json['id'], identifier)

    ##############################################################
    # Test CSV Renderer
    ##############################################################
    def test_csv_renderer(self):
        """Test FactCollectionCSVRenderer."""
        renderer = FactCollectionCSVRenderer()
        # Test no FC id
        test_json = {}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        # Test doesn't exist
        test_json = {'id': 42}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        request_json = {'sources':
                        [{'source_id': self.net_source.id,
                          'source_type': self.net_source.source_type,
                          'facts': [{'key': 'value'}]}]}

        response_json = self.create_expect_201(
            request_json)
        test_json = copy.deepcopy(response_json)
        csv_result = renderer.render(test_json)
        expected = 'Report,Number Sources\r\n1,1\r\n\r\n\r\n'\
            'Source\r\nid,name,type\r\n1,test_source,network\r\nFacts\r\nkey'\
            '\r\nvalue\r\n\r\n\r\n'
        self.assertEqual(csv_result, expected)

        # Test cached works too
        test_json = copy.deepcopy(response_json)
        test_json['sources'][0]['facts'] = []
        csv_result = renderer.render(test_json)
        expected = 'Report,Number Sources\r\n1,1\r\n\r\n\r\n'\
            'Source\r\nid,name,type\r\n1,test_source,network\r\nFacts\r\nkey'\
            '\r\nvalue\r\n\r\n\r\n'
        # These would be different if not cached
        self.assertEqual(csv_result, expected)

        # Clear cache
        fact_collection = FactCollection.objects.get(id=response_json['id'])
        fact_collection.csv_content = None
        fact_collection.save()

        # Remove sources
        test_json = copy.deepcopy(response_json)
        test_json['sources'] = None
        csv_result = renderer.render(test_json)
        expected = 'Report,Number Sources\r\n1,0\r\n'
        self.assertEqual(csv_result, expected)

        # Clear cache
        fact_collection = FactCollection.objects.get(id=response_json['id'])
        fact_collection.csv_content = None
        fact_collection.save()

        # Remove sources
        test_json = copy.deepcopy(response_json)
        test_json['sources'] = []
        csv_result = renderer.render(test_json)
        expected = 'Report,Number Sources\r\n1,0\r\n\r\n\r\n'
        self.assertEqual(csv_result, expected)

        # Clear cache
        fact_collection = FactCollection.objects.get(id=response_json['id'])
        fact_collection.csv_content = None
        fact_collection.save()

        # Remove facts
        test_json = copy.deepcopy(response_json)
        test_json['sources'][0]['facts'] = []
        csv_result = renderer.render(test_json)
        expected = 'Report,Number Sources\r\n1,1\r\n\r\n\r\n'\
            'Source\r\nid,name,type\r\n1,test_source,network\r\nFacts\r\n'\
            '\r\n'
        self.assertEqual(csv_result, expected)


class DeploymentReportTest(TestCase):
    """Tests against the Deployment reports function."""

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
                'uname_hostname': '1.2.3.4',
                'virt_virt': 'virt-guest',
                'virt_type': 'vmware',
                'virt_num_guests': 1,
                'virt_num_running_guests': 1,
                'virt_what_type': 'vt'
            }
            facts.append(fact_json)
        fact_collection = self.create_fact_collection_expect_201(fc_json)
        return fact_collection

    def test_get_fact_collection_group_report_count(self):
        """Get a specific group count report."""
        url = '/api/v1/reports/1/deployments/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        filters = {'group_count': 'os_release'}
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.assertIsInstance(report, dict)
        self.assertEqual(report['report'][0]['count'], 2)
        self.assertEqual(report['report'][1]['count'], 1)

    def test_get_fact_collection_group_report(self):
        """Get a specific group count report."""
        url = '/api/v1/reports/1/deployments/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.assertIsInstance(report, dict)
        self.assertEqual(len(report['report'][0].keys()), 32)

    def test_get_fact_collection_filter_report(self):
        """Get a specific group count report with filter."""
        url = '/api/v1/reports/1/deployments/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        filters = {'os_name': True,
                   'os_release': 'true'}
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.assertIsInstance(report, dict)
        self.assertEqual(report['report'][0],
                         {'os_name': 'RHEL', 'os_release': 'RHEL 7.4'})

    def test_get_fact_collection_404(self):
        """Fail to get a report for missing collection."""
        url = '/api/v1/reports/2/deployments/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_fact_collection_bad_id(self):
        """Fail to get a report for missing collection."""
        url = '/api/v1/reports/string/deployments/'

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    def test_group_count_400_invalid_field(self):
        """Fail to get report with invalid field for group_count."""
        url = '/api/v1/reports/1/deployments/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        response = self.client.get(url, {'group_count': 'no_field'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_group_count_invalid_combo_400(self):
        """Fail to get report due to invalid filter combo."""
        url = '/api/v1/reports/1/deployments/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        filters = {'group_count': 'os_release', 'os_name': 'true'}
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_group_count_invalid_combo2_400(self):
        """Fail to get report due to invalid filter combo."""
        url = '/api/v1/reports/1/deployments/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        filters = {'group_count': 'os_release',
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
        url = '/api/v1/reports/1/deployments/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()

        csv_result = renderer.render(report)

        # pylint: disable=line-too-long
        expected = 'Report\r\n1\r\n\r\n\r\nReport:\r\narchitecture,bios_uuid,cpu_core_count,cpu_count,cpu_socket_count,detection-network,detection-satellite,detection-vcenter,entitlements,infrastructure_type,ip_addresses,is_redhat,jboss brms,jboss eap,jboss fuse,mac_addresses,name,os_name,os_release,os_version,redhat_certs,redhat_package_count,sources,subscription_manager_id,system_creation_date,system_last_checkin_date,virtualized_type,vm_cluster,vm_datacenter,vm_dns_name,vm_host,vm_host_socket_count,vm_state,vm_uuid\r\n,,2.0,2,2,True,False,False,,virtualized,,,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,2017-07-18,,vmware,,,,,,,\r\n,,2.0,2,2,True,False,False,,virtualized,,,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,2017-07-18,,vmware,,,,,,,\r\n,,2.0,2,2,True,False,False,,virtualized,,,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.5,7.5,,,[test_source],,2017-07-18,,vmware,,,,,,,\r\n\r\n' # noqa
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
        filters = {'name': True}
        url = '/api/v1/reports/1/deployments/'
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()

        print(report)
        csv_result = renderer.render(report)

        # pylint: disable=line-too-long
        expected = 'Report\r\n1\r\n\r\n\r\nReport:\r\nname\r\n1.2.3.4\r\n1.2.3.4\r\n1.2.3.4\r\n\r\n'  # noqa
        self.assertEqual(csv_result, expected)
