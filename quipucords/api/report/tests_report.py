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

import copy
import json
import uuid
from unittest.mock import patch

from api import messages
from api.models import (Credential,
                        FactCollection,
                        ServerInformation,
                        Source)
from api.report.renderer import (DeploymentCSVRenderer,
                                 DetailsCSVRenderer,
                                 sanitize_row)

from django.core import management
from django.test import TestCase
from django.urls import reverse

from rest_framework import status


class DetailReportTest(TestCase):
    """Tests against the Detail reports function."""

    def setUp(self):
        """Create test case setup."""
        management.call_command('flush', '--no-input')
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
        self.server_id = ServerInformation.create_or_retreive_server_id()

    def tearDown(self):
        """Create test case tearDown."""
        pass

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
                        [{'server_id': self.server_id,
                          'source_name': self.net_source.name,
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
        """Test DetailsCSVRenderer."""
        renderer = DetailsCSVRenderer()
        # Test no FC id
        test_json = {}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        # Test doesn't exist
        test_json = {'id': 42}
        value = renderer.render(test_json)
        self.assertIsNone(value)

        request_json = {'sources':
                        [{'server_id': self.server_id,
                          'source_name': self.net_source.name,
                          'source_type': self.net_source.source_type,
                          'facts': [{'key': 'value'}]}]}

        response_json = self.create_expect_201(
            request_json)
        test_json = copy.deepcopy(response_json)
        csv_result = renderer.render(test_json)
        # pylint: disable=line-too-long
        expected = 'Report,Number Sources\r\n1,1\r\n\r\n\r\nSource\r\nServer Identifier,Source Name,Source Type\r\n%s,test_source,network\r\nFacts\r\nkey\r\nvalue\r\n\r\n\r\n' % self.server_id  # noqa
        self.assertEqual(csv_result, expected)

        # Test cached works too
        test_json = copy.deepcopy(response_json)
        test_json['sources'][0]['facts'] = []
        csv_result = renderer.render(test_json)
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
        # pylint: disable=line-too-long
        expected = 'Report,Number Sources\r\n1,1\r\n\r\n\r\nSource\r\nServer Identifier,Source Name,Source Type\r\n%s,test_source,network\r\nFacts\r\n\r\n' % self.server_id  # noqa
        self.assertEqual(csv_result, expected)


class DeploymentReportTest(TestCase):
    """Tests against the Deployment reports function."""

    # pylint: disable= no-self-use, invalid-name
    def setUp(self):
        """Create test case setup."""
        management.call_command('flush', '--no-input')
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
        self.server_id = ServerInformation.create_or_retreive_server_id()

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
        fc_json = {'sources': [{'server_id': self.server_id,
                                'source_name': self.net_source.name,
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
        expected = [{'os_name': 'RHEL', 'os_release': 'RHEL 7.4'},
                    {'os_name': 'RHEL', 'os_release': 'RHEL 7.5'}]
        diff = [x for x in expected if x not in report['report']]
        self.assertEqual(diff, [])

    def test_get_fact_collection_404(self):
        """Fail to get a report for missing collection."""
        url = '/api/v1/reports/2/deployments/'

        # Create a system fingerprint via collection receiver
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_bad_deployment_report(self):
        """Test case where FactCollection exists but no fingerprint."""
        url = '/api/v1/reports/1/deployments/'

        # Create a system fingerprint via collection receiver
        facts = []
        fc_json = {'sources': [{'server_id': self.server_id,
                                'source_name': self.net_source.name,
                                'source_type': self.net_source.source_type,
                                'facts': facts}]}

        fact_json = {
            'cpu_core_count': 'cat',
        }
        facts.append(fact_json)
        self.create_fact_collection_expect_201(fc_json)

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code,
                         status.HTTP_424_FAILED_DEPENDENCY)

    def test_get_fact_collection_bad_id(self):
        """Fail to get a report for missing collection."""
        url = '/api/v1/reports/string/deployments/'

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND)

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
    def test_sanitize_row(self):
        """Test sanitize_row function."""
        self.assertEqual(sanitize_row(['data', None, 'data,data']),
                         ['data', None, 'data;data'])

    def test_csv_renderer(self):
        """Test DeploymentCSVRenderer."""
        renderer = DeploymentCSVRenderer()
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
        data_rows = [",,2.0,2,2,True,False,False,,virtualized,,,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,2017-07-18,,vmware,,,,,,,",  # noqa
                     # pylint: disable=line-too-long
                     ",,2.0,2,2,True,False,False,,virtualized,,,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.4,7.4,,,[test_source],,2017-07-18,,vmware,,,,,,,",  # noqa
                     # pylint: disable=line-too-long
                     ",,2.0,2,2,True,False,False,,virtualized,,,absent,absent,absent,absent,,1.2.3.4,RHEL,RHEL 7.5,7.5,,,[test_source],,2017-07-18,,vmware,,,,,,,",  # noqa
                     # pylint: disable=line-too-long
                     "architecture,bios_uuid,cpu_core_count,cpu_count,cpu_socket_count,detection-network,detection-satellite,detection-vcenter,entitlements,infrastructure_type,ip_addresses,is_redhat,jboss brms,jboss eap,jboss fuse,jboss web server,mac_addresses,name,os_name,os_release,os_version,redhat_certs,redhat_package_count,sources,subscription_manager_id,system_creation_date,system_last_checkin_date,virtualized_type,vm_cluster,vm_datacenter,vm_dns_name,vm_host,vm_host_socket_count,vm_state,vm_uuid"]  # noqa
        for row in data_rows:
            result = row in csv_result
            self.assertEqual(result, True)

    def test_csv_renderer_only_name(self):
        """Test DeploymentCSVRenderer name filter."""
        renderer = DeploymentCSVRenderer()
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

        csv_result = renderer.render(report)

        # pylint: disable=line-too-long
        expected = 'Report\r\n1\r\n\r\n\r\nReport:\r\nname\r\n1.2.3.4\r\n1.2.3.4\r\n1.2.3.4\r\n\r\n'  # noqa
        self.assertEqual(csv_result, expected)


class SyncMergeReports(TestCase):
    """Tests merging reports synchronously."""

    # pylint: disable= no-self-use, invalid-name
    def setUp(self):
        """Create test case setup."""
        management.call_command('flush', '--no-input')
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
        self.server_id = ServerInformation.create_or_retreive_server_id()

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

    ##############################################################
    # Test Report Merge
    ##############################################################
    def test_sync_merge_empty_body(self):
        """Test sync merge with empty body."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_REQUIRED]})

    def test_sync_merge_empty_dict(self):
        """Test sync merge with empty dict."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_REQUIRED]})

    def test_sync_merge_jobs_not_list(self):
        """Test sync merge with not list."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': 5}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_NOT_LIST]})

    def test_sync_merge_jobs_list_too_short(self):
        """Test sync merge with list too short."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': [5]}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_TOO_SHORT]})

    def test_sync_merge_jobs_list_contains_string(self):
        """Test sync merge with containing str."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': [5, 'hello']}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_NOT_INT]})

    def test_sync_merge_jobs_list_contains_duplicates(self):
        """Test sync merge with containing duplicates."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': [5, 5]}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports': [messages.REPORT_MERGE_NOT_UNIQUE]})

    def test_sync_merge_jobs_list_contains_invalid_job_ids(self):
        """Test sync merge with containing duplicates."""
        # pylint: disable=no-member
        url = '/api/v1/reports/merge/'
        data = {'reports': [5, 6]}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_response = response.json()
        self.assertEqual(
            json_response, {'reports':
                            [messages.REPORT_MERGE_NOT_FOUND % '5, 6']})

    def test_sync_merge_jobs_success(self):
        """Test sync merge jobs success."""
        url = reverse('facts-list')
        sources1 = [{'server_id': self.server_id,
                     'source_name': self.net_source.name,
                     'source_type': self.net_source.source_type,
                     'facts': [{'key1': 'value1'}]}]
        sources2 = [{'server_id': 'abc',
                     'source_name': 'another_name',
                     'source_type': 'network',
                     'facts': [{'key2': 'value2'}]}]
        request_json = {'sources': sources1}
        response = self.client.post(url,
                                    json.dumps(request_json),
                                    'application/json')
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        response_json = response.json()
        self.assertEqual(
            response_json['sources'],
            sources1)
        report1_id = response_json['id']

        request_json = {'sources': sources2}
        response = self.client.post(url,
                                    json.dumps(request_json),
                                    'application/json')
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        response_json = response.json()
        self.assertEqual(
            response_json['sources'],
            sources2)
        report2_id = response_json['id']

        url = '/api/v1/reports/merge/'
        data = {'reports': [report1_id, report2_id]}
        response = self.client.put(url, json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        json_response = response.json()
        expected = {'id': 3,
                    'sources': [
                        {'server_id': 'abc',
                         'source_name': 'another_name',
                         'source_type': 'network',
                         'facts': [{'key2': 'value2'}]},
                        {'server_id': self.server_id,
                         'source_name': 'test_source',
                         'source_type': 'network',
                         'facts': [{'key1': 'value1'}]}],
                    'status': 'complete'}

        self.assertEqual(
            json_response, expected)


def dummy_start():
    """Create a dummy method for testing."""
    pass


class AsyncMergeReports(TestCase):
    """Tests against the Deployment reports function."""

    # pylint: disable= no-self-use, invalid-name
    def setUp(self):
        """Create test case setup."""
        management.call_command('flush', '--no-input')
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
        self.server_id = ServerInformation.create_or_retreive_server_id()

    def create_report_merge_job(self, data):
        """Call the create endpoint."""
        url = '/api/v1/reports/merge/jobs/'
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_report_merge_job_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_report_merge_job(data)
        if response.status_code != status.HTTP_201_CREATED:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()

    def create_report_merge_job_expect_400(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_report_merge_job(data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return response.json()

    ##############################################################
    # Test Async Report Merge
    ##############################################################

    @patch('api.report.view.start_scan', side_effect=dummy_start)
    def test_greenpath_create(self, start_scan):
        """Create report merge job object via API."""
        # pylint: disable=unused-argument
        request_json = {'sources':
                        [{'server_id': self.server_id,
                          'source_name': self.net_source.name,
                          'source_type': self.net_source.source_type,
                          'facts': [{'key': 'value'}]}]}

        response_json = self.create_report_merge_job_expect_201(
            request_json)

        expected = {
            'scan_type': 'fingerprint',
            'status': 'created',
            'status_message': 'Job is created.'
        }
        self.assertIn('id', response_json)
        job_id = response_json.pop('id')
        self.assertEqual(response_json, expected)

        url = '/api/v1/reports/merge/jobs/{}/'.format(job_id)
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code,
                         status.HTTP_200_OK)

    def test_create_report_merge_bad_url(self):
        """Create merge report job bad url."""
        url = '/api/v1/reports/merge/jobs/1/'
        get_response = self.client.post(url)
        self.assertEqual(get_response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_missing_sources(self):
        """Test missing sources attribute."""
        request_json = {}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(
            response_json['sources'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_empty_sources(self):
        """Test empty sources attribute."""
        request_json = {'sources': []}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(
            response_json['sources'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_missing_name(self):
        """Test source is missing source_name."""
        request_json = {'sources': [{'foo': 'abc'}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_name'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_empty_name(self):
        """Test source has empty source_name."""
        request_json = {'sources': [{'source_name': ''}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_name'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_name_not_string(self):
        """Test source has source_name that is not a string."""
        request_json = {'sources': [{'server_id': self.server_id,
                                     'source_name': 100,
                                     'source_type':
                                     self.net_source.source_type}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_name'],
            messages.FC_SOURCE_NAME_NOT_STR)

    def test_missing_source_type(self):
        """Test source_type is missing."""
        request_json = {'sources': [
            {'source_name': self.net_source.name}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_type'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_empty_source_type(self):
        """Test source_type is empty."""
        request_json = {'sources':
                        [{'source_id': self.net_source.id,
                          'source_type': ''}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_type'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_invalid_source_type(self):
        """Test source_type has invalid_value."""
        request_json = {'sources':
                        [{'server_id': self.server_id,
                          'source_name': self.net_source.name,
                          'source_type': 'abc'}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)

        valid_choices = ', '.join(
            [valid_type[0] for valid_type in Source.SOURCE_TYPE_CHOICES])

        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['source_type'],
            messages.FC_MUST_BE_ONE_OF % valid_choices)

    def test_source_missing_facts(self):
        """Test source missing facts attr."""
        request_json = {'sources':
                        [{'source_name': self.net_source.name,
                          'source_type': self.net_source.source_type}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['facts'],
            messages.FC_REQUIRED_ATTRIBUTE)

    def test_source_empty_facts(self):
        """Test source has empty facts list."""
        request_json = {'sources':
                        [{'source_name': self.net_source.name,
                          'source_type': self.net_source.source_type,
                          'facts': []}]}
        response_json = self.create_report_merge_job_expect_400(
            request_json)
        self.assertEqual(len(response_json['valid_sources']), 0)
        self.assertEqual(len(response_json['invalid_sources']), 1)
        self.assertEqual(
            response_json['invalid_sources'][0]['errors']['facts'],
            messages.FC_REQUIRED_ATTRIBUTE)
