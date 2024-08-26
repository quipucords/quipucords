"""Test the satellite connect task."""

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
from scanner.satellite.connect import ConnectTaskRunner
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


class TestConnectTaskRunner:
    """Tests Satellite connect capabilities."""

    def setup_method(self, _test_method):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            cred_type=DataSources.SATELLITE,
            username="username",
            password="password",
            become_password=None,
            become_method=None,
            become_user=None,
            ssh_keyfile=None,
        )
        self.cred.save()

        self.source = Source(name="source1", port=443, hosts=["1.2.3.4"])
        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT
        )

    @pytest.mark.django_db
    def test_run_unknown_sat(self):
        """Test the running connect task for unknown sat version."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch(
            "scanner.satellite.runner.utils.status", return_value=(None, None, None)
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_sat6_bad_status(self):
        """Test the running connect task for Sat 6 with bad status."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch(
            "scanner.satellite.runner.utils.status",
            return_value=(401, None, SATELLITE_VERSION_6),
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_sat6_bad_api_version(self):
        """Test the running connect task for Sat6 with bad api version."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch(
            "scanner.satellite.runner.utils.status",
            return_value=(200, 3, SATELLITE_VERSION_6),
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_conn_err(self):
        """Test the running connect task with connection error."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch(
            "scanner.satellite.runner.utils.status", side_effect=mock_conn_exception
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_sat_err(self):
        """Test the running connect task with satellite error."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch(
            "scanner.satellite.runner.utils.status", side_effect=SatelliteError()
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_auth_err(self):
        """Test the running connect task with satellite auth error."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch(
            "scanner.satellite.runner.utils.status",
            side_effect=mock_sat_auth_exception,
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_with_timeout_err(self):
        """Test the running connect task with timeout error."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch(
            "scanner.satellite.runner.utils.status", side_effect=mock_timeout_error
        ) as mock_sat_status:
            status = task.run()
            mock_sat_status.assert_called_once_with(ANY)
            assert status[1] == ScanTask.FAILED

    @pytest.mark.django_db
    def test_run_sat6_v2(self):
        """Test the running connect task for Sat6 with api version 2."""
        task = ConnectTaskRunner(self.scan_job, self.scan_task)

        with patch(
            "scanner.satellite.runner.utils.status",
            return_value=(200, 2, SATELLITE_VERSION_6),
        ) as mock_sat_status:
            with patch.object(
                SatelliteSixV2, "host_count", return_value=1
            ) as mock_host_count:
                with patch.object(
                    SatelliteSixV2, "hosts", return_value=["sys1"]
                ) as mock_hosts:
                    status = task.run()
                    mock_sat_status.assert_called_once_with(ANY)
                    mock_host_count.assert_called_once_with()
                    mock_hosts.assert_called_once_with()
                    assert status[1] == ScanTask.COMPLETED
