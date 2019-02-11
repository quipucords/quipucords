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
"""Test the reports API."""

import json
import sys
import tarfile

from api.common.common_report import create_report_version
from api.models import (Credential,
                        ServerInformation,
                        Source)
from api.reports.reports_gzip_renderer import ReportsGzipRenderer

from django.core import management
from django.test import TestCase
from django.urls import reverse

from rest_framework import status


class ReportsTest(TestCase):
    """Tests against the Reports function."""

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
        self.report_version = create_report_version()
        self.details_json = None
        self.deployments_json = None
        self.insights_json = None

    def tearDown(self):
        """Create test case tearDown."""
        pass

    def create_details_report(self, data):
        """Call the create endpoint."""
        url = reverse('reports-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_details_report_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_details_report(data)
        if response.status_code != status.HTTP_201_CREATED:
            print('Failure cause: ')
            print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        details_json = response.json()
        self.details_json = details_json
        return details_json

    def create_details_report_expect_400(self, data):
        """Create a source, return the response as a dict."""
        response = self.create_details_report(data)
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
        fc_json = {'report_type': 'details',
                   'sources': [{'server_id': self.server_id,
                                'report_version': create_report_version(),
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
                'connection_uuid': '834c8f3b-5015-4156-bfb7-286d3ffe11b4',
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
                'virt_what_type': 'vt',
                'system_platform_id': '834c8f3b-5015-4156-bfb7-286d3ffe11b5',
                'ifconfig_ip_addresses': ['1.2.3.4']
            }
            facts.append(fact_json)
        details_report = self.create_details_report_expect_201(fc_json)
        return details_report

    def create_reports_dict(self):
        """Create a deployments report."""
        url = '/api/v1/reports/1/deployments/'
        url2 = '/api/v1/reports/1/insights/'
        self.generate_fingerprints(
            os_versions=['7.4', '7.4', '7.5'])
        filters = {'group_count': 'os_release'}
        response = self.client.get(url, filters)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        report = response.json()
        self.deployments_json = report
        response2 = self.client.get(url2)
        insights_report = response2.json()
        self.insights_json = insights_report
        reports_dict = dict()
        reports_dict['report_id'] = 1
        reports_dict['details_json'] = self.details_json
        reports_dict['deployments_json'] = self.deployments_json
        reports_dict['insights_json'] = self.insights_json
        return reports_dict

    def test_reports_gzip_renderer(self):
        """Get a tar.gz return for report_id via API."""
        # pylint: disable=line-too-long
        reports_dict = self.create_reports_dict()
        deployments_csv = 'Report ID,Report Type,Report Version,Report Platform ID\r\n1,deployments,%s,%s\r\n\r\n\r\nSystem Fingerprints:\r\narchitecture,bios_uuid,count,cpu_core_count,cpu_count,cpu_socket_count,detection-network,detection-satellite,detection-vcenter,entitlements,etc_machine_id,infrastructure_type,insights_client_id,ip_addresses,is_redhat,mac_addresses,name,os_name,os_release,os_version,redhat_certs,redhat_package_count,sources,subscription_manager_id,system_addons,system_creation_date,system_last_checkin_date,system_role,system_service_level_agreement,system_usage_type,virtualized_type,vm_cluster,vm_datacenter,vm_dns_name,vm_host,vm_host_core_count,vm_host_socket_count,vm_state,vm_uuid\r\n,,2,,,,,,,,,,,,,,,,RHEL 7.4,,,,,,,,,,,,,,,,,,,,\r\n,,1,,,,,,,,,,,,,,,,RHEL 7.5,,,,,,,,,,,,,,,,,,,,\r\n\r\n' % (self.report_version, reports_dict.get('deployments_json').get('report_platform_id'))  # noqa

        # pylint: disable=line-too-long
        details_csv = 'Report ID,Report Type,Report Version,Report Platform ID,Number Sources\r\n1,details,%s,%s,1\r\n\r\n\r\nSource\r\nServer Identifier,Source Name,Source Type\r\n%s,test_source,network\r\nFacts\r\nconnection_host,connection_port,connection_uuid,cpu_core_count,cpu_core_per_socket,cpu_count,cpu_hyperthreading,cpu_siblings,cpu_socket_count,date_anaconda_log,date_yum_history,etc_release_name,etc_release_release,etc_release_version,ifconfig_ip_addresses,system_platform_id,uname_hostname,virt_num_guests,virt_num_running_guests,virt_type,virt_virt,virt_what_type\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.4,7.4,[1.2.3.4],834c8f3b-5015-4156-bfb7-286d3ffe11b5,1.2.3.4,1,1,vmware,virt-guest,vt\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.4,7.4,[1.2.3.4],834c8f3b-5015-4156-bfb7-286d3ffe11b5,1.2.3.4,1,1,vmware,virt-guest,vt\r\n1.2.3.4,22,834c8f3b-5015-4156-bfb7-286d3ffe11b4,2,1,2,False,1,2,2017-07-18,2017-07-18,RHEL,RHEL 7.5,7.5,[1.2.3.4],834c8f3b-5015-4156-bfb7-286d3ffe11b5,1.2.3.4,1,1,vmware,virt-guest,vt\r\n\r\n\r\n' % (self.report_version, reports_dict.get('details_json').get('report_platform_id'), self.server_id) # noqa

        renderer = ReportsGzipRenderer()
        tar_gz_result = renderer.render(reports_dict)
        self.assertNotEqual(tar_gz_result, None)
        tar = tarfile.open(fileobj=tar_gz_result)
        files = tar.getmembers()
        filenames = tar.getnames()
        self.assertEqual(len(files), 5)
        # tar.getnames() always returns same order as tar.getmembers()
        for idx, file in enumerate(files):
            file_contents = tar.extractfile(file).read().decode()
            if filenames[idx].endswith('csv'):
                if 'details' in file_contents:
                    self.assertEqual(file_contents, details_csv)
                elif 'deployments' in file_contents:
                    self.assertEqual(file_contents, deployments_csv)
                else:
                    sys.exit('Could not identify .csv return.')
            else:
                tar_json = json.loads(file_contents)
                tar_json_type = tar_json.get('report_type')
                if tar_json_type == 'details':
                    self.assertEqual(tar_json, self.details_json)
                elif tar_json_type == 'deployments':
                    self.assertEqual(tar_json, self.deployments_json)
                elif tar_json_type == 'insights':
                    self.assertEqual(tar_json, self.insights_json)
                else:
                    sys.exit('Could not identify .json return')

    def test_reports_gzip_renderer_no_insights(self):
        """Make sure there is no insights report if it is not in the dict."""
        reports_dict = self.create_reports_dict()
        reports_dict.pop('insights_json')
        renderer = ReportsGzipRenderer()
        tar_gz_result = renderer.render(reports_dict)
        self.assertNotEqual(tar_gz_result, None)
        tar = tarfile.open(fileobj=tar_gz_result)
        files = tar.getmembers()
        # make sure there are only 4 files
        self.assertEqual(len(files), 4)
