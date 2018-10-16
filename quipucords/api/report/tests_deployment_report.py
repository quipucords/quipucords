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

from api.models import (Credential,
                        ServerInformation,
                        Source)
from api.report.cvs_renderer import (DeploymentCSVRenderer,
                                     sanitize_row)

from django.core import management
from django.test import TestCase
from django.urls import reverse

from rest_framework import status


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

    def create_fact_collection_expect_400(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_fact_collection(data)
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return response.json()

    def generate_fingerprints(self,
                              os_name='RHEL',
                              os_versions=None):
        """Create a DetailsReport for test."""
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
        details_report = self.create_fact_collection_expect_201(fc_json)
        return details_report

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
        self.assertEqual(report['system_fingerprints'][0]['count'], 2)
        self.assertEqual(report['system_fingerprints'][1]['count'], 1)

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
        self.assertEqual(len(report['system_fingerprints'][0].keys()), 14)

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
        diff = [x for x in expected if x not in report['system_fingerprints']]
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
        """Test case where DetailsReport exists but no fingerprint."""
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
        self.create_fact_collection_expect_400(fc_json)

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
        data_rows = ["2,2,2,True,False,False,,virtualized,absent,absent,absent,absent,1.2.3.4,RHEL,RHEL 7.4,7.4,[test_source],2017-07-18,vmware",  # noqa
                     # pylint: disable=line-too-long
                     "2,2,2,True,False,False,,virtualized,absent,absent,absent,absent,1.2.3.4,RHEL,RHEL 7.4,7.4,[test_source],2017-07-18,vmware",  # noqa
                     # pylint: disable=line-too-long
                     "2,2,2,True,False,False,,virtualized,absent,absent,absent,absent,1.2.3.4,RHEL,RHEL 7.5,7.5,[test_source],2017-07-18,vmware",  # noqa
                     # pylint: disable=line-too-long
                     "cpu_core_count,cpu_count,cpu_socket_count,detection-network,detection-satellite,detection-vcenter,entitlements,infrastructure_type,jboss brms,jboss eap,jboss fuse,jboss web server,name,os_name,os_release,os_version,sources,system_creation_date,virtualized_type"]  # noqa
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
