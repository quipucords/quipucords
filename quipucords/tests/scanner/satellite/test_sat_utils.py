"""Test the satellite utils."""
import xmlrpc.client
from unittest.mock import ANY, patch

import pytest
import requests_mock

from api.models import Credential, ScanTask, Source
from constants import DataSources
from scanner.satellite.api import (
    SATELLITE_VERSION_5,
    SATELLITE_VERSION_6,
    SatelliteAuthException,
    SatelliteException,
)
from scanner.satellite.utils import (
    _status5,
    construct_url,
    data_map,
    execute_request,
    get_connect_data,
    get_credential,
    get_sat5_client,
    status,
    validate_task_stats,
)
from tests.scanner.test_util import create_scan_job


def mock_xml_fault(param1, param2):
    """Mock method to throw connection error."""
    raise xmlrpc.client.Fault(faultCode=500, faultString="fault")


class TestSatelliteUtils:
    """Tests Satellite utils functions."""

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

        self.source = Source(
            name="source1", port=443, hosts=["1.2.3.4"], ssl_cert_verify=False
        )
        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, scan_type=ScanTask.SCAN_TYPE_CONNECT
        )

    @pytest.mark.django_db
    def test_get_credential(self):
        """Test the method to extract credential."""
        cred = get_credential(self.scan_task)
        assert cred == self.cred

    @pytest.mark.django_db
    def test_get_connect_data(self):
        """Test method to get connection data from task."""
        host, port, user, password = get_connect_data(self.scan_task)
        assert host == "1.2.3.4"
        assert port == 443
        assert user == "username"
        assert password == "password"

    @pytest.mark.django_db
    def test_construct_url(self):
        """Test method to construct satellite url."""
        expected = "https://1.2.3.4:443/api/status"
        status_url = "https://{sat_host}:{port}/api/status"
        url = construct_url(status_url, "1.2.3.4")
        assert url == expected

    @pytest.mark.django_db
    def test_execute_request(self):
        """Test the method to execute a request against a satellite server."""
        status_url = "https://{sat_host}:{port}/api/status"
        with requests_mock.Mocker() as mocker:
            url = construct_url(status_url, "1.2.3.4")
            jsonresult = {"api_version": 2}
            mocker.get(url, status_code=200, json=jsonresult)
            response, formatted_url = execute_request(self.scan_task, status_url)
            assert url == formatted_url
            assert response.status_code == 200
            assert response.json() == jsonresult

    @patch(
        "scanner.satellite.utils._status6",
        return_value=(200, SATELLITE_VERSION_6, SATELLITE_VERSION_6),
    )
    @pytest.mark.django_db
    def test_status_sat6(self, mock_status5):
        """Test a patched status request to Satellite 6 server."""
        status_code, api_version, satellite_version = status(self.scan_task)
        assert status_code == 200
        assert api_version == SATELLITE_VERSION_6
        assert satellite_version == SATELLITE_VERSION_6
        mock_status5.assert_called_once_with(ANY)

    @pytest.mark.django_db
    @patch("xmlrpc.client.ServerProxy")
    def test_status5(self, mock_serverproxy):
        """Test a successful status request to Satellite 5 server."""
        client = mock_serverproxy.return_value
        client.auth.login.return_value = "key"
        client.auth.logout.return_value = "key"
        status_code, api_version, satellite_version = _status5(self.scan_task)
        assert status_code == 200
        assert api_version == SATELLITE_VERSION_5
        assert satellite_version == SATELLITE_VERSION_5

    @pytest.mark.django_db
    @patch("xmlrpc.client.ServerProxy")
    def test_status5_xmlfault(self, mock_serverproxy):
        """Test a successful status request to Satellite 5 server."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        with pytest.raises(SatelliteException):
            _status5(self.scan_task)
            mock_serverproxy.auth.login.assert_called_once_with(ANY, ANY)

    @pytest.mark.django_db
    @patch("xmlrpc.client.ServerProxy")
    def test_status(self, mock_serverproxy):
        """Test a successful status request to Satellite server."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        with requests_mock.Mocker() as mocker:
            status_url = "https://{sat_host}:{port}/api/status"
            url = construct_url(status_url, "1.2.3.4")
            jsonresult = {"api_version": 2}
            mocker.get(url, status_code=200, json=jsonresult)
            status_code, api_version, satellite_version = status(self.scan_task)
            assert status_code == 200
            assert api_version == 2
            assert satellite_version == SATELLITE_VERSION_6

    @pytest.mark.django_db
    @patch("xmlrpc.client.ServerProxy")
    def test_status_error(self, mock_serverproxy):
        """Test a error status request to Satellite server."""
        client = mock_serverproxy.return_value
        client.auth.login.side_effect = mock_xml_fault
        with requests_mock.Mocker() as mocker:
            status_url = "https://{sat_host}:{port}/api/status"
            url = construct_url(status_url, "1.2.3.4")
            jsonresult = {"api_version": 2}
            mocker.get(url, status_code=401, json=jsonresult)
            with pytest.raises(SatelliteAuthException):
                status(self.scan_task)
                mock_serverproxy.auth.login.assert_called_once_with(ANY, ANY)

    @pytest.mark.django_db
    def test_data_map(self):
        """Test a mapping of data from a response dictionary."""
        map_dict = {"id": "uuid", "color": "new::color"}
        data = {"uuid": "100", "new::color": "blue", "key": "value"}
        expected = {"id": "100", "color": "blue"}
        mapped = data_map(map_dict, data)
        assert mapped == expected

    @pytest.mark.django_db
    def test_get_sat5_client(self):
        """Test the sat5 client helper."""
        client, user, password = get_sat5_client(self.scan_task)
        assert client is not None
        assert user == "username"
        assert password == "password"

    @pytest.mark.django_db
    def test_validate_task_stats(self):
        """Test validate task stats no errors."""
        validate_task_stats(self.scan_task)

    @pytest.mark.django_db
    def test_validate_task_stats_error(self):
        """Test validate task stats errors."""
        with pytest.raises(SatelliteException):
            self.scan_task.increment_stats("TEST", increment_sys_count=True)
            validate_task_stats(self.scan_task)
