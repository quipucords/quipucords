"""Test the satellite inspect task."""

from unittest.mock import ANY, patch

import pytest
from requests import exceptions

from api.models import Credential, ScanTask, Source
from constants import DataSources
from scanner.satellite.api import (
    SATELLITE_VERSION_6,
    SatelliteAuthError,
    SatelliteError,
)
from scanner.satellite.inspect import InspectTaskRunner
from scanner.satellite.six import SatelliteSixV2
from tests.scanner.test_util import create_scan_job


def mock_conn_exception(param1):
    """Mock method to throw connection error."""
    raise exceptions.ConnectionError()


def mock_sat_auth_exception(param1):
    """Mock method to throw satellite auth error."""
    raise SatelliteAuthError()


def mock_timeout_error(param1):
    """Mock method to throw timeout error."""
    raise TimeoutError()


def mock_exception(param1, param2):
    """Mock method to throw exception."""
    raise Exception()


class TestInspectTaskRunner:
    """Tests Satellite connect capabilities."""

    def setup_method(self, _test_method):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            cred_type=DataSources.SATELLITE,
            username="username",
            password="password",
        )
        self.cred.save()

        self.source = Source(name="source1", port=443, hosts=["1.2.3.4"])

        self.source.save()
        self.source.credentials.add(self.cred)

    def create_scan_job(self):
        """Create scan job for tests."""
        scan_job, inspect_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT
        )

        inspect_task.update_stats("TEST_SAT.", sys_scanned=0)
        return scan_job, inspect_task

    @pytest.mark.django_db
    def test_run_unknown_sat(self):
        """Test running the inspect scan for unknown sat."""
        scan_job, inspect_task = self.create_scan_job()
        task = InspectTaskRunner(scan_job, inspect_task)
        with patch(
            "scanner.satellite.runner.utils.status", return_value=(None, None, None)
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_sat6_bad_status(self):
        """Test the running inspect task for Sat 6 with bad status."""
        scan_job, inspect_task = self.create_scan_job()
        task = InspectTaskRunner(scan_job, inspect_task)

        with patch(
            "scanner.satellite.runner.utils.status",
            return_value=(401, None, SATELLITE_VERSION_6),
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_sat6_bad_api_version(self):
        """Test the running inspect task for Sat6 with bad api version."""
        scan_job, inspect_task = self.create_scan_job()
        task = InspectTaskRunner(scan_job, inspect_task)

        with patch(
            "scanner.satellite.runner.utils.status",
            return_value=(200, 3, SATELLITE_VERSION_6),
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_conn_err(self):
        """Test the running inspect task with connection error."""
        scan_job, inspect_task = self.create_scan_job()
        task = InspectTaskRunner(scan_job, inspect_task)

        with patch(
            "scanner.satellite.runner.utils.status", side_effect=mock_conn_exception
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_auth_err(self):
        """Test the running inspect task with satellite auth error."""
        scan_job, inspect_task = self.create_scan_job()
        task = InspectTaskRunner(scan_job, inspect_task)

        with patch(
            "scanner.satellite.runner.utils.status",
            side_effect=mock_sat_auth_exception,
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_sat_err(self):
        """Test the running inspect task with satellite error."""
        scan_job, inspect_task = self.create_scan_job()
        task = InspectTaskRunner(scan_job, inspect_task)

        with patch(
            "scanner.satellite.runner.utils.status", side_effect=SatelliteError()
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_timeout(self):
        """Test the running inspect task with timeout error."""
        scan_job, inspect_task = self.create_scan_job()
        task = InspectTaskRunner(scan_job, inspect_task)

        with patch(
            "scanner.satellite.runner.utils.status", side_effect=mock_timeout_error
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_excep(self):
        """Test the running inspect task with general exception."""
        scan_job, inspect_task = self.create_scan_job()
        task = InspectTaskRunner(scan_job, inspect_task)

        with patch(
            "scanner.satellite.runner.utils.status", side_effect=mock_exception
        ) as mock_sat_status:
            with pytest.raises(Exception):
                status = task.run()
                mock_sat_status.assert_called_once_with(ANY)
                assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_sat(self):
        """Test the running inspect task with satellite."""
        scan_job, inspect_task = self.create_scan_job()
        task = InspectTaskRunner(scan_job, inspect_task)

        with (
            patch(
                "scanner.satellite.runner.utils.status",
                return_value=(200, 2, SATELLITE_VERSION_6),
            ) as mock_sat_status,
            patch.object(SatelliteSixV2, "host_count") as mock_host_count,
            patch.object(SatelliteSixV2, "hosts") as mock_hosts,
            patch.object(SatelliteSixV2, "hosts_facts") as mock_facts,
        ):
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            mock_host_count.assert_called_once_with()
            mock_hosts.assert_called_once_with()
            mock_facts.assert_called_once_with()
            assert status[1] == ScanTask.COMPLETED
