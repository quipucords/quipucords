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
"""Test the vcenter connect capabilities."""

from django.test import TestCase
from api.models import (Credential, Source, HostRange, ScanTask,
                        ScanJob, ConnectionResults)
from scanner.vcenter.connect import ConnectTaskRunner


class ConnectTaskRunnerTest(TestCase):
    """Tests against the ConnectTaskRunner class and functions."""

    runner = None

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
        self.runner = ConnectTaskRunner(scan_job=self.scan_job,
                                        scan_task=self.scan_task,
                                        conn_results=self.conn_results)

    def tearDown(self):
        """Cleanup test case setup."""
        pass

    def test_store_connect_data(self):
        """Test the connection data method."""
        vm_names = ['vm1', 'vm2']
        # pylint: disable=protected-access
        self.runner._store_connect_data(vm_names, self.cred)
        self.assertEqual(len(self.conn_results.results.all()), 1)
        result = self.conn_results.results.all().first()
        self.assertEqual(result.scan_task, self.scan_task)
        self.assertEqual(result.source, self.source)
