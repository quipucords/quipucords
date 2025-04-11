"""Test the satellite factory."""

import pytest

from api.models import Credential, ScanTask, Source
from constants import DataSources
from scanner.satellite.factory import create
from scanner.satellite.six import SatelliteSixV1, SatelliteSixV2
from scanner.satellite.utils import SATELLITE_VERSION_6
from tests.scanner.test_util import create_scan_job


class TestSatelliteFactory:
    """Tests Satellite factory functions."""

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
            self.source, scan_type=ScanTask.SCAN_TYPE_INSPECT
        )

    @pytest.mark.django_db
    def test_create_sat_none(self):
        """Test the method to fail to create a Sat interface."""
        satellite_version = None
        api_version = 1
        api = create(satellite_version, api_version, self.scan_job, self.scan_task)
        assert api is None

    @pytest.mark.django_db
    def test_create_sat6_v1(self):
        """Test the method to create a Sat 6 interface."""
        satellite_version = SATELLITE_VERSION_6
        api_version = 1
        api = create(satellite_version, api_version, self.scan_job, self.scan_task)
        assert api.__class__ == SatelliteSixV1

    @pytest.mark.django_db
    def test_create_sat6_v2(self):
        """Test the method to create a Sat 6 interface."""
        satellite_version = SATELLITE_VERSION_6
        api_version = 2
        api = create(satellite_version, api_version, self.scan_job, self.scan_task)
        assert api.__class__ == SatelliteSixV2

    @pytest.mark.django_db
    def test_create_sat6_unknown(self):
        """Test the method to create a Sat 6 interface."""
        satellite_version = SATELLITE_VERSION_6
        api_version = 9
        api = create(satellite_version, api_version, self.scan_job, self.scan_task)
        assert api is None
