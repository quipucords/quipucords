#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the insights report endpoint."""

import json
import uuid
from unittest.mock import patch

from api.common.common_report import (create_filename,
                                      create_report_version)
from api.insights_report.view import _create_report_slices
from api.models import DeploymentsReport

from django.core import management
from django.test import TestCase

from rest_framework import status


class InsightsReportTest(TestCase):
    """Tests against the Insights reports function."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Create test case setup."""
        management.call_command('flush', '--no-input')
        self.report_version = create_report_version()
        self.connection_uuid = str(uuid.uuid4())
        self.fingerprints = \
            [{
                'connection_host': '1.2.3.4',
                'connection_port': 22,
                'connection_uuid': self.connection_uuid,
                'cpu_count': 2,
                'cpu_core_per_socket': 1,
                'cpu_siblings': 1,
                'cpu_hyperthreading': False,
                'cpu_socket_count': 2,
                'cpu_core_count': 2,
                'date_anaconda_log': '2017-07-18',
                'date_yum_history': '2017-07-18',
                'etc_release_name': '',
                'etc_release_version': '',
                'etc_release_release': '',
                'uname_hostname': '1.2.3.4',
                'virt_virt': 'virt-guest',
                'virt_type': 'vmware',
                'virt_num_guests': 1,
                'virt_num_running_guests': 1,
                'virt_what_type': 'vt',
                'ip_addresses': ['1.2.3.4']}]
        self.insights_hosts = [
            {
                'display_name': 'dhcp181-116.gsslab.rdu2.redhat.com',
                'fqdn': 'dhcp181-116.gsslab.rdu2.redhat.com',
                'bios_uuid': 'F1011E42-F121-ED73-0BB8-9CF9E721FC0A',
                'ip_addresses': [
                    '10.10.181.116'
                ],
                'mac_addresses': [
                    '00:50:56:9e:7b:19'
                ],
                'subscription_manager_id':
                    'F1011E42-F121-ED73-0BB8-9CF9E721FC0A',
                'facts': [
                    {
                        'namespace': 'qpc',
                        'facts': {
                            'bios_uuid':
                                'F1011E42-F121-ED73-0BB8-9CF9E721FC0A',
                            'ip_addresses': [
                                '10.10.181.116'
                            ],
                            'mac_addresses': [
                                '00:50:56:9e:7b:19'
                            ],
                            'subscription_manager_id':
                                'F1011E42-F121-ED73-0BB8-9CF9E721FC0A',
                            'name': 'dhcp181-116.gsslab.rdu2.redhat.com',
                            'os_release':
                                'Red Hat Enterprise Linux \
                                Server release 5.9 (Tikanga)',
                            'os_version': '5.9 (Tikanga)',
                            'infrastructure_type': 'virtualized',
                            'cpu_count': 1,
                            'architecture': 'x86_64',
                            'is_redhat': True,
                            'redhat_certs': '69.pem',
                            'cpu_socket_count': 1,
                            'cpu_core_count': 1
                        },
                        'rh_product_certs': [],
                        'rh_products_installed': [
                            'RHEL',
                            'EAP',
                            'FUSE'
                        ]
                    }
                ]
            }
        ]
        self.deployments_report = DeploymentsReport(
            id=1, report_id=1, report_version=self.report_version,
            status=DeploymentsReport.STATUS_COMPLETE,
            cached_insights=None,
            cached_fingerprints=json.dumps(self.fingerprints))

    def test_get_insights_report_200_exists(self):
        """Retrieve insights report."""
        url = '/api/v1/reports/1/insights/'
        expected_hosts = [{'unique_id': i} for i in range(10001)]
        self.deployments_report.cached_insights = json.dumps(
            expected_hosts)
        self.deployments_report.save()
        with patch('api.insights_report.view.get_object_or_404',
                   return_value=self.deployments_report):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        self.assertIn(create_filename('metadata', 'json', 1),
                      response_json.keys())
        report_slices = {}
        for key in response_json:
            self.assertIn('report_id_1/', key)
            if key != 'report_id_1/metadata.json':
                report_slices[key] = response_json[key]
        # metadata slice number_hosts matches the actual
        # number of hosts in a slice
        report_slices_in_metadata = \
            response_json['report_id_1/metadata.json']['report_slices']
        total_returned_hosts_num = 0
        for key_1, key_2 in zip(report_slices_in_metadata, report_slices):
            self.assertEqual(report_slices_in_metadata[key_1]['number_hosts'],
                             len(report_slices[key_2]['hosts']))
            # used later to check for the total size
            total_returned_hosts_num += len(report_slices[key_2]['hosts'])
        # no hosts lost
        returned_host_ids = {host['unique_id'] for slice_key in report_slices
                             for host in report_slices[slice_key]['hosts']}
        expected_host_ids = {host['unique_id'] for host in expected_hosts}
        self.assertSetEqual(returned_host_ids, expected_host_ids)
        # sum of all hosts in a slice is equal to
        # the total number of host (before call)
        self.assertEqual(total_returned_hosts_num, len(expected_hosts))

    def test_get_insights_report_200_generate_exists(self):
        """Retrieve insights report."""
        url = '/api/v1/reports/1/insights/'
        self.deployments_report.cached_insights = json.dumps(
            self.insights_hosts)
        self.deployments_report.save()
        with patch('api.insights_report.view.get_object_or_404',
                   return_value=self.deployments_report):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        self.assertIn(create_filename('metadata', 'json', 1),
                      response_json.keys())
        for key in response_json:
            self.assertIn('report_id_1/', key)

    def test_get_insights_report_404_no_canonical(self):
        """Retrieve insights report."""
        url = '/api/v1/reports/1/insights/'
        no_canonical = [{
            'connection_host': '1.2.3.4',
            'connection_port': 22,
            'connection_uuid': self.connection_uuid,
            'cpu_count': 2,
            'cpu_core_per_socket': 1,
            'cpu_siblings': 1,
            'cpu_hyperthreading': False,
            'cpu_socket_count': 2,
            'cpu_core_count': 2,
            'date_anaconda_log': '2017-07-18',
            'date_yum_history': '2017-07-18',
            'etc_release_name': '',
            'etc_release_version': '',
            'etc_release_release': '',
            'uname_hostname': '1.2.3.4',
            'virt_virt': 'virt-guest',
            'virt_type': 'vmware',
            'virt_num_guests': 1,
            'virt_num_running_guests': 1,
            'virt_what_type': 'vt'
        }]
        self.deployments_report.cached_insights = None
        self.deployments_report.cached_fingerprints = json.dumps(no_canonical)
        self.deployments_report.save()
        with patch('api.insights_report.view.get_object_or_404',
                   return_value=self.deployments_report):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_insights_report_404_missing(self):
        """Check that legacy report without insights returns 404."""
        url = '/api/v1/reports/1/insights/'
        fingerprints = [{'connection_host': '1.2.3.4',
                         'connection_port': 22,
                         'connection_uuid': self.connection_uuid,
                         'cpu_count': 2,
                         'cpu_core_per_socket': 1,
                         'cpu_siblings': 1,
                         'cpu_hyperthreading': False,
                         'cpu_socket_count': 2,
                         'cpu_core_count': 2,
                         'date_anaconda_log': '2017-07-18',
                         'date_yum_history': '2017-07-18',
                         'etc_release_name': '',
                         'etc_release_version': '',
                         'etc_release_release': '',
                         'uname_hostname': '1.2.3.4',
                         'virt_virt': 'virt-guest',
                         'virt_type': 'vmware',
                         'virt_num_guests': 1,
                         'virt_num_running_guests': 1,
                         'virt_what_type': 'vt',
                         'mac_addresses': ['1.2.3.4']},
                        {'connection_host': '1.2.3.4',
                         'connection_port': 22,
                         'connection_uuid': self.connection_uuid,
                         'cpu_count': 2,
                         'cpu_core_per_socket': 1,
                         'cpu_siblings': 1,
                         'cpu_hyperthreading': False,
                         'cpu_socket_count': 2,
                         'cpu_core_count': 2,
                         'date_anaconda_log': '2017-07-18',
                         'date_yum_history': '2017-07-18',
                         'etc_release_name': '',
                         'etc_release_version': '',
                         'etc_release_release': '',
                         'uname_hostname': '1.2.3.4',
                         'virt_virt': 'virt-guest',
                         'virt_type': 'vmware',
                         'virt_num_guests': 1,
                         'virt_num_running_guests': 1,
                         'virt_what_type': 'vt',
                         'mac_addresses': ['1.2.3.4']}]

        self.deployments_report.cached_insights = None
        self.deployments_report.cached_fingerprints = json.dumps(fingerprints)
        self.deployments_report.save()
        with patch('api.insights_report.view.get_object_or_404',
                   return_value=self.deployments_report):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_insights_report_no_hosts(self):
        """Check that api returns 404 if there are no hosts."""
        response = _create_report_slices(self.deployments_report, [])
        self.assertEqual(response.status_code, 404)

    def test_get_insights_report_bad_id(self):
        """Fail to get a report for bad id."""
        url = '/api/v1/reports/string/insights/'

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND)

    def test_get_insights_nonexistent(self):
        """Fail to get a report for report id that doesn't exist."""
        url = '/api/v1/reports/2/insights/'

        # Query API
        response = self.client.get(url)
        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND)
