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
"""Test the satellite factory."""

from django.test import TestCase
from api.models import (Credential, Source, ScanTask,
                        ScanJob, JobConnectionResult, TaskConnectionResult,
                        SourceOptions)
from scanner.satellite.factory import create
from scanner.satellite.six import SatelliteSixV1, SatelliteSixV2
from scanner.satellite.five import SatelliteFive


class SatelliteFactoryTest(TestCase):
    """Tests Satellite factory functions."""

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

        self.scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                                  source=self.source, sequence_number=1)
        self.scan_task.save()

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.scan_job.save()
        self.scan_job.tasks.add(self.scan_task)
        self.conn_results = JobConnectionResult()
        self.conn_results.save()
        self.scan_job.connection_results = self.conn_results
        self.scan_job.save()
        self.conn_result = TaskConnectionResult()
        self.conn_result.save()

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_create_sat_none(self):
        """Test the method to fail to create a Sat interface."""
        satellite_version = None
        api_version = 1
        api = create(satellite_version, api_version,
                     self.scan_task)
        self.assertEqual(api, None)

    def test_create_sat5(self):
        """Test the method to create a Sat 5 interface."""
        satellite_version = SourceOptions.SATELLITE_VERSION_5
        api_version = 1
        api = create(satellite_version, api_version,
                     self.scan_task)
        self.assertEqual(api.__class__, SatelliteFive)

    def test_create_sat6_v1(self):
        """Test the method to create a Sat 6 interface."""
        satellite_version = SourceOptions.SATELLITE_VERSION_62
        api_version = 1
        api = create(satellite_version, api_version,
                     self.scan_task)
        self.assertEqual(api.__class__, SatelliteSixV1)

    def test_create_sat6_v2(self):
        """Test the method to create a Sat 6 interface."""
        satellite_version = SourceOptions.SATELLITE_VERSION_62
        api_version = 2
        api = create(satellite_version, api_version,
                     self.scan_task)
        self.assertEqual(api.__class__, SatelliteSixV2)

    def test_create_sat6_unknown(self):
        """Test the method to create a Sat 6 interface."""
        satellite_version = SourceOptions.SATELLITE_VERSION_62
        api_version = 9
        api = create(satellite_version, api_version,
                     self.scan_task)
        self.assertEqual(api, None)
