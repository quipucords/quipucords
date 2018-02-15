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
"""Test the satellite inspect task."""

from datetime import datetime
from unittest.mock import patch, ANY
from django.test import TestCase
from requests import exceptions
from api.models import (Credential, Source, ScanTask,
                        ScanJob, JobConnectionResult, TaskConnectionResult,
                        JobInspectionResult, SourceOptions)
from scanner.satellite.inspect import InspectTaskRunner
from scanner.satellite.six import SatelliteSixV2
from scanner.satellite.api import SatelliteException


def mock_conn_exception(param1):  # pylint: disable=unused-argument
    """Mock method to throw connection error."""
    raise exceptions.ConnectionError()


def mock_sat_exception(param1):  # pylint: disable=unused-argument
    """Mock method to throw satellite error."""
    raise SatelliteException()


def mock_timeout_error(param1):  # pylint: disable=unused-argument
    """Mock method to throw timeout error."""
    raise TimeoutError()


def mock_exception(param1):  # pylint: disable=unused-argument
    """Mock method to throw exception."""
    raise Exception()


# pylint: disable=too-many-instance-attributes
class InspectTaskRunnerTest(TestCase):
    """Tests Satellite connect capabilities."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            cred_type=Credential.SATELLITE_CRED_TYPE,
            username='username',
            password='password')
        self.cred.save()

        self.source = Source(
            name='source1',
            port=443,
            hosts='["1.2.3.4"]')

        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_INSPECT,
                                  source=self.source, sequence_number=2,
                                  start_time=datetime.utcnow())
        self.scan_task.save()
        self.scan_task.update_stats('TEST_SAT.', sys_scanned=0)

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.scan_job.save()
        self.scan_job.tasks.add(self.scan_task)
        self.conn_results = JobConnectionResult()
        self.conn_results.save()
        self.scan_job.connection_results = self.conn_results

        self.conn_result = TaskConnectionResult(
            scan_task=self.scan_task, source=self.source)
        self.conn_result.save()

        conn_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                             source=self.source, sequence_number=1,
                             start_time=datetime.utcnow())
        conn_task.complete()
        self.scan_task.prerequisites.add(conn_task)
        self.inspect_results = JobInspectionResult()
        self.inspect_results.save()
        self.scan_job.inspection_results = self.inspect_results

        self.scan_job.save()

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_run_failed_prereq(self):
        """Test the running connect task with no source options."""
        self.scan_task.prerequisites.all().delete()
        conn_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                             source=self.source, sequence_number=1)
        conn_task.status = ScanTask.FAILED
        conn_task.save()
        self.scan_task.prerequisites.add(conn_task)
        task = InspectTaskRunner(self.scan_job, self.scan_task)
        status = task.run()

        self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_no_source_options(self):
        """Test the running connect task with no source options."""
        task = InspectTaskRunner(self.scan_job, self.scan_task)
        status = task.run()

        self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_sat5_bad_status(self):
        """Test the running connect task for Satellite 5."""
        options = SourceOptions(
            satellite_version=SourceOptions.SATELLITE_VERSION_5)
        options.save()
        self.source.options = options
        self.source.save()
        task = InspectTaskRunner(self.scan_job, self.scan_task)
        with patch('scanner.satellite.connect.utils.status',
                   return_value=(401, None)) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY, ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_sat6_bad_status(self):
        """Test the running connect task for Sat 6 with bad status."""
        options = SourceOptions(
            satellite_version=SourceOptions.SATELLITE_VERSION_62)
        options.save()
        self.source.options = options
        self.source.save()
        task = InspectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   return_value=(401, None)) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY, ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_sat6_bad_api_version(self):
        """Test the running connect task for Sat6 with bad api version."""
        options = SourceOptions(
            satellite_version=SourceOptions.SATELLITE_VERSION_62)
        options.save()
        self.source.options = options
        self.source.save()
        task = InspectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   return_value=(200, 3)) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY, ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_with_conn_err(self):
        """Test the running connect task with connection error."""
        options = SourceOptions(
            satellite_version=SourceOptions.SATELLITE_VERSION_62)
        options.save()
        self.source.options = options
        self.source.save()
        task = InspectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   side_effect=mock_conn_exception) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY, ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_with_sat_err(self):
        """Test the running connect task with satellite error."""
        options = SourceOptions(
            satellite_version=SourceOptions.SATELLITE_VERSION_62)
        options.save()
        self.source.options = options
        self.source.save()
        task = InspectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   side_effect=mock_sat_exception) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY, ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_with_timeout(self):
        """Test the running connect task with timeout error."""
        options = SourceOptions(
            satellite_version=SourceOptions.SATELLITE_VERSION_62)
        options.save()
        self.source.options = options
        self.source.save()
        task = InspectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   side_effect=mock_timeout_error) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY, ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_with_excep(self):
        """Test the running connect task with general exception."""
        options = SourceOptions(
            satellite_version=SourceOptions.SATELLITE_VERSION_62)
        options.save()
        self.source.options = options
        self.source.save()
        task = InspectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   side_effect=mock_exception) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY, ANY)
            self.assertEqual(status[1], ScanTask.FAILED)

    def test_run_with_sat(self):
        """Test the running connect task with satellite."""
        options = SourceOptions(
            satellite_version=SourceOptions.SATELLITE_VERSION_62)
        options.save()
        self.source.options = options
        self.source.save()
        task = InspectTaskRunner(self.scan_job, self.scan_task)

        with patch('scanner.satellite.connect.utils.status',
                   return_value=(200, 2)) as mock_sat_status:
            with patch.object(SatelliteSixV2, 'hosts_facts') as mock_facts:
                status = task.run()
                mock_sat_status.assert_called_once_with(ANY, ANY)
                mock_facts.assert_called_once_with()
                self.assertEqual(status[1], ScanTask.COMPLETED)
