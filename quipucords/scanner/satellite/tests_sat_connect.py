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
"""Test the satellite connect task."""

from multiprocessing import Value
from unittest.mock import ANY, patch

from django.test import TestCase

from requests import exceptions

from api.models import (Credential,  # noqa I100
                        ScanJob,
                        ScanTask,
                        Source)

from scanner.satellite.api import (SATELLITE_VERSION_5,
                                   SATELLITE_VERSION_6,
                                   SatelliteAuthException,
                                   SatelliteException)
from scanner.satellite.connect import ConnectTaskRunner
from scanner.satellite.six import SatelliteSixV2
from scanner.test_util import create_scan_job


def mock_conn_exception(param1):  # pylint: disable=unused-argument
    """Mock method to throw connection error."""
    raise exceptions.ConnectionError()


def mock_sat_auth_exception(param1):  # pylint: disable=unused-argument
    """Mock method to throw satellite auth error."""
    raise SatelliteAuthException()


def mock_sat_exception(param1):  # pylint: disable=unused-argument
    """Mock method to throw satellite error."""
    raise SatelliteException()


def mock_timeout_error(param1):  # pylint: disable=unused-argument
    """Mock method to throw timeout error."""
    raise TimeoutError()


class ConnectTaskRunnerTest(TestCase):
    """Tests Satellite connect capabilities."""

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
            port=443,
            hosts='["1.2.3.4"]')
        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT)

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_run_sat5_bad_status(self):
        """Test the running connect task for Satellite 5."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)
        with patch('scanner.satellite.connect.utils.status',
                   return_value=(401,
                                 None,
                                 SATELLITE_VERSION_5)) as mock_sat_status:
            status = task.run(Value('i', ScanJob.JOB_RUN))
            mock_sat_status.assert_called_once_with(ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_sat6_bad_status(self):
        """Test the running connect task for Sat 6 with bad status."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   return_value=(401,
                                 None,
                                 SATELLITE_VERSION_6)) as mock_sat_status:
            status = task.run(Value('i', ScanJob.JOB_RUN))
            mock_sat_status.assert_called_once_with(ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_sat6_bad_api_version(self):
        """Test the running connect task for Sat6 with bad api version."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   return_value=(200,
                                 3,
                                 SATELLITE_VERSION_6)) as mock_sat_status:
            status = task.run(Value('i', ScanJob.JOB_RUN))
            mock_sat_status.assert_called_once_with(ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_with_conn_err(self):
        """Test the running connect task with connection error."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   side_effect=mock_conn_exception) as mock_sat_status:
            status = task.run(Value('i', ScanJob.JOB_RUN))
            mock_sat_status.assert_called_once_with(ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_with_sat_err(self):
        """Test the running connect task with satellite error."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   side_effect=mock_sat_exception) as mock_sat_status:
            status = task.run(Value('i', ScanJob.JOB_RUN))
            mock_sat_status.assert_called_once_with(ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_with_auth_err(self):
        """Test the running connect task with satellite auth error."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   side_effect=mock_sat_auth_exception) as mock_sat_status:
            status = task.run(Value('i', ScanJob.JOB_RUN))
            mock_sat_status.assert_called_once_with(ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_with_timeout_err(self):
        """Test the running connect task with timeout error."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   side_effect=mock_timeout_error) as mock_sat_status:
            status = task.run(Value('i', ScanJob.JOB_RUN))
            mock_sat_status.assert_called_once_with(ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_sat6_v2(self):
        """Test the running connect task for Sat6 with api version 2."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   return_value=(200,
                                 2,
                                 SATELLITE_VERSION_6)) as mock_sat_status:
            with patch.object(SatelliteSixV2, 'host_count',
                              return_value=1) as mock_host_count:
                with patch.object(SatelliteSixV2, 'hosts',
                                  return_value=['sys1']) as mock_hosts:
                    status = task.run(Value('i', ScanJob.JOB_RUN))
                    mock_sat_status.assert_called_once_with(ANY)
                    mock_host_count.assert_called_once_with()
                    mock_hosts.assert_called_once_with()
                    self.assertEqual(status[1], ScanTask.COMPLETED)

    def test_run_sat6_v2_cancel(self):
        """Test the running connect task (cancel)."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        status = task.run(Value('i', ScanJob.JOB_TERMINATE_CANCEL))
        self.assertEqual(status[1], ScanTask.CANCELED)

    def test_run_sat6_v2_pause(self):
        """Test the running connect task (pause)."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        status = task.run(Value('i', ScanJob.JOB_TERMINATE_PAUSE))
        self.assertEqual(status[1], ScanTask.PAUSED)
