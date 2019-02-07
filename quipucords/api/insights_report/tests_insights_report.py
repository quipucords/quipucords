#
# Copyright (c) 2017-2019 Red Hat, Inc.
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

from api.common.common_report import create_report_version
from api.models import DeploymentsReport

from django.core import management
from django.test import TestCase

from rest_framework import status


class InsightsReportTest(TestCase):
    """Tests against the Insights reports function."""

    # pylint: disable= no-self-use, invalid-name
    def setUp(self):
        """Create test case setup."""
        management.call_command('flush', '--no-input')
        self.report_version = create_report_version()
        self.sys_platform_id = str(uuid.uuid4())
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
                'system_platform_id': self.sys_platform_id,
                'ip_addresses': ['1.2.3.4']}]
        self.deployments_report = DeploymentsReport(
            id=1, report_id=1, report_version=self.report_version,
            status=DeploymentsReport.STATUS_COMPLETE,
            cached_insights=None,
            cached_fingerprints=json.dumps(self.fingerprints))

    def test_get_insights_report_200_generate(self):
        """Retrieve insights report."""
        url = '/api/v1/reports/1/insights/'
        expected_hosts = {
            self.sys_platform_id: {
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
                'ip_addresses': ['1.2.3.4']}}

        with patch('api.insights_report.view.get_object_or_404',
                   return_value=self.deployments_report):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_hosts, response.json().get('hosts'))

    def test_get_insights_report_200_exists(self):
        """Retrieve insights report."""
        url = '/api/v1/reports/1/insights/'
        expected_hosts = {
            self.sys_platform_id:
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
                 'ip_addresses': ['4.3.2.1']}}
        self.deployments_report.cached_insights = json.dumps(expected_hosts)
        self.deployments_report.save()
        with patch('api.insights_report.view.get_object_or_404',
                   return_value=self.deployments_report):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_hosts, response.json().get('hosts'))

    def test_get_insights_report_200_generate_exists(self):
        """Retrieve insights report."""
        url = '/api/v1/reports/1/insights/'
        expected_hosts = {
            self.sys_platform_id:
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
                 'ip_addresses': ['4.3.2.1']}}
        self.deployments_report.cached_insights = json.dumps(expected_hosts)
        self.deployments_report.save()
        with patch('api.insights_report.view.get_object_or_404',
                   return_value=self.deployments_report):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_hosts, response.json().get('hosts'))

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
            'virt_what_type': 'vt',
            'system_platform_id': self.sys_platform_id
        }]
        self.deployments_report.cached_insights = None
        self.deployments_report.cached_fingerprints = json.dumps(no_canonical)
        self.deployments_report.save()
        with patch('api.insights_report.view.get_object_or_404',
                   return_value=self.deployments_report):
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_insights_report_404_missing_sys_id(self):
        """Check that system fingerprints missing system platform id fail."""
        url = '/api/v1/reports/1/insights/'
        no_canonical = \
            [{'connection_host': '1.2.3.4',
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
              'mac_addresses': ['1.2.3.4'],
              'system_platform_id': self.sys_platform_id}]

        expected_hosts = {
            self.sys_platform_id:
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
                 'mac_addresses': ['1.2.3.4']}}
        self.deployments_report.cached_insights = None
        self.deployments_report.cached_fingerprints = json.dumps(no_canonical)
        self.deployments_report.save()
        with patch('api.insights_report.view.get_object_or_404',
                   return_value=self.deployments_report):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_hosts, response.json().get('hosts'))

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
