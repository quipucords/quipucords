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
"""Test the satellite six interface."""

from unittest.mock import patch
import requests_mock
from django.test import TestCase
from api.models import (Credential, Source, HostRange, ScanTask,
                        ScanJob, ConnectionResults, ConnectionResult)
from scanner.satellite.utils import construct_url
from scanner.satellite.api import SatelliteException
from scanner.satellite.six import SatelliteSixV1, SatelliteSixV2


# pylint: disable=too-many-instance-attributes
class SatelliteSixV1Test(TestCase):
    """Tests Satellite 6 v1 functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            cred_type=Credential.SATELLITE_CRED_TYPE,
            username='username',
            password='password',
            become_password=None,
            become_method=None,
            become_user=None,
            ssh_keyfile=None)
        self.cred.save()

        self.source = Source(
            name='source1',
            port=443)
        self.source.save()
        self.source.credentials.add(self.cred)

        self.host = HostRange(host_range='1.2.3.4',
                              source_id=self.source.id)
        self.host.save()

        self.source.hosts.add(self.host)

        self.scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                                  source=self.source, sequence_number=1)
        self.scan_task.save()

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.scan_job.save()
        self.scan_job.tasks.add(self.scan_task)
        self.conn_results = ConnectionResults(scan_job=self.scan_job)
        self.conn_results.save()
        self.conn_result = ConnectionResult(
            scan_task=self.scan_task, source=self.source)
        self.conn_result.save()

        self.api = SatelliteSixV1(self.scan_task, self.conn_result)

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_get_orgs(self):
        """Test the method to get orgs."""
        orgs_url = 'https://{sat_host}:{port}/katello/api/v2/organizations'
        with requests_mock.Mocker() as mocker:
            url = construct_url(orgs_url, '1.2.3.4')
            jsonresult = {'results': [{'id': 1}, {'id': 7}, {'id': 8}],
                          'per_page': 100}
            mocker.get(url, status_code=200, json=jsonresult)
            orgs = self.api.get_orgs()
            orgs2 = self.api.get_orgs()
            self.assertEqual(orgs, [1, 7, 8])
            self.assertEqual(orgs, orgs2)

    def test_get_orgs_with_err(self):
        """Test the method to get orgs with err."""
        orgs_url = 'https://{sat_host}:{port}/katello/api/v2/organizations'
        with requests_mock.Mocker() as mocker:
            url = construct_url(orgs_url, '1.2.3.4')
            jsonresult = {'results': [{'id': 1}, {'id': 7}, {'id': 8}],
                          'per_page': 100}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.get_orgs()

    @patch('scanner.satellite.six.SatelliteSixV1.get_orgs')
    def test_host_count(self, mock_get_orgs):
        """Test the method host_count."""
        mock_get_orgs.return_value = [1]
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            self.assertEqual(systems_count, 3)

    @patch('scanner.satellite.six.SatelliteSixV1.get_orgs')
    def test_host_count_with_err(self, mock_get_orgs):
        """Test the method host_count with err."""
        mock_get_orgs.return_value = [1]
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.host_count()

    @patch('scanner.satellite.six.SatelliteSixV1.get_orgs')
    def test_hosts(self, mock_get_orgs):
        """Test the method hosts."""
        mock_get_orgs.return_value = [1]
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            hosts = self.api.hosts()
            self.assertEqual(systems_count, 3)
            self.assertEqual(len(hosts), 3)
            self.assertEqual(hosts, ['sys1', 'sys2', 'sys3'])

    @patch('scanner.satellite.six.SatelliteSixV1.get_orgs')
    def test_hosts_with_err(self, mock_get_orgs):
        """Test the method hosts."""
        mock_get_orgs.return_value = [1]
        hosts_url = 'https://{sat_host}:{port}/katello/api' \
            '/v2/organizations/{org_id}/systems'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.hosts()


# pylint: disable=too-many-instance-attributes
class SatelliteSixV2Test(TestCase):
    """Tests Satellite 6 v2 functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            cred_type=Credential.SATELLITE_CRED_TYPE,
            username='username',
            password='password',
            become_password=None,
            become_method=None,
            become_user=None,
            ssh_keyfile=None)
        self.cred.save()

        self.source = Source(
            name='source1',
            port=443)
        self.source.save()
        self.source.credentials.add(self.cred)

        self.host = HostRange(host_range='1.2.3.4',
                              source_id=self.source.id)
        self.host.save()

        self.source.hosts.add(self.host)

        self.scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                                  source=self.source, sequence_number=1)
        self.scan_task.save()

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.scan_job.save()
        self.scan_job.tasks.add(self.scan_task)
        self.conn_results = ConnectionResults(scan_job=self.scan_job)
        self.conn_results.save()
        self.conn_result = ConnectionResult(
            scan_task=self.scan_task, source=self.source)
        self.conn_result.save()

        self.api = SatelliteSixV2(self.scan_task, self.conn_result)

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_host_count(self):
        """Test the method host_count."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            self.assertEqual(systems_count, 3)

    def test_host_count_with_err(self):
        """Test the method host_count with error."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.host_count()

    def test_hosts(self):
        """Test the method hosts."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=200, json=jsonresult)
            systems_count = self.api.host_count()
            hosts = self.api.hosts()
            self.assertEqual(systems_count, 3)
            self.assertEqual(len(hosts), 3)
            self.assertEqual(hosts, ['sys1', 'sys2', 'sys3'])

    def test_hosts_with_err(self):
        """Test the method hosts with error."""
        hosts_url = 'https://{sat_host}:{port}/api/v2/hosts'
        with requests_mock.Mocker() as mocker:
            url = construct_url(url=hosts_url, sat_host='1.2.3.4', org_id=1)
            jsonresult = {'results': [{'name': 'sys1'},
                                      {'name': 'sys2'},
                                      {'name': 'sys3'}],
                          'per_page': 100,
                          'total': 3}
            mocker.get(url, status_code=500, json=jsonresult)
            with self.assertRaises(SatelliteException):
                self.api.hosts()
