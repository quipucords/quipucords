#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the vcenter utils."""

from unittest.mock import Mock, patch, ANY
from django.test import TestCase
from api.models import (Credential, Source, HostRange, ScanTask,
                        ScanJob, ConnectionResults)
from scanner.vcenter.utils import vcenter_connect


class VCenterUtilsTest(TestCase):
    """Tests VCenter utils functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred.save()

        self.source = Source(
            name='source1',
            port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

        self.host = HostRange(host_range='1.2.3.4',
                              source_id=self.source.id)
        self.host.save()

        self.source.hosts.add(self.host)

        self.scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_INSPECT,
                                  source=self.source, sequence_number=2)
        self.scan_task.save()

        self.scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_INSPECT)
        self.scan_job.save()
        self.scan_job.tasks.add(self.scan_task)
        self.conn_results = ConnectionResults(scan_job=self.scan_job)
        self.conn_results.save()

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_vcenter_connect(self):
        """Test the connection method."""
        mock_vcenter = Mock()
        with patch('scanner.vcenter.utils.SmartConnectNoSSL',
                   return_value=mock_vcenter) as mock_smart_connect:
            vcenter = vcenter_connect(self.scan_task)
            self.assertEqual(mock_vcenter, vcenter)
            mock_smart_connect.assert_called_once_with(
                host=ANY, user=ANY, pwd=ANY, port=ANY)
