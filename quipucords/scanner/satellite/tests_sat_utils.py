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
"""Test the satellite utils."""

import requests_mock
from django.test import TestCase
from api.models import (Credential, Source, HostRange, ScanTask,
                        ScanJob, ConnectionResults)
from scanner.satellite.utils import (get_credential, get_connect_data,
                                     construct_url, execute_request,
                                     status)


class SatelliteUtilsTest(TestCase):
    """Tests Satellite utils functions."""

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

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_get_credential(self):
        """Test the method to extract credential."""
        cred = get_credential(self.scan_task)
        self.assertEqual(cred, self.cred)

    def test_get_connect_data(self):
        """Test method to get connection data from task."""
        host, port, user, password = get_connect_data(self.scan_task)
        self.assertEqual(host, '1.2.3.4')
        self.assertEqual(port, 443)
        self.assertEqual(user, 'username')
        self.assertEqual(password, 'password')

    def test_construct_url(self):
        """Test method to construct satellite url."""
        expected = 'https://1.2.3.4:443/api/status'
        status_url = 'https://{sat_host}:{port}/api/status'
        url = construct_url(status_url, '1.2.3.4')
        self.assertEqual(url, expected)

    def test_execute_request(self):
        """Test the method to execute a request against a satellite server."""
        status_url = 'https://{sat_host}:{port}/api/status'
        with requests_mock.Mocker() as mocker:
            url = construct_url(status_url, '1.2.3.4')
            jsonresult = {'api_version': 2}
            mocker.get(url, status_code=200, json=jsonresult)
            response, formatted_url = execute_request(self.scan_task,
                                                      status_url)
            self.assertEqual(url, formatted_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), jsonresult)

    def test_status(self):
        """Test a successful status request to Satellite server."""
        with requests_mock.Mocker() as mocker:
            status_url = 'https://{sat_host}:{port}/api/status'
            url = construct_url(status_url, '1.2.3.4')
            jsonresult = {'api_version': 2}
            mocker.get(url, status_code=200, json=jsonresult)
            status_code, api_version = status(self.scan_task)

            self.assertEqual(status_code, 200)
            self.assertEqual(api_version, 2)

    def test_status_error(self):
        """Test a error status request to Satellite server."""
        with requests_mock.Mocker() as mocker:
            status_url = 'https://{sat_host}:{port}/api/status'
            url = construct_url(status_url, '1.2.3.4')
            jsonresult = {'api_version': 2}
            mocker.get(url, status_code=401, json=jsonresult)
            status_code, api_version = status(self.scan_task)

            self.assertEqual(status_code, 401)
            self.assertEqual(api_version, None)
