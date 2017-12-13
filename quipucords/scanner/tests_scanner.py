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
"""Test the scanner capabilities."""

from django.test import TestCase
from django.core.urlresolvers import reverse
from api.models import (Credential, Source, HostRange,
                        ScanTask, ScanJob)
from scanner.job import ScanJobRunner


class ScannerTest(TestCase):
    """Tests against the HostScanner class and functions."""

    # pylint: disable=too-many-instance-attributes
    def setUp(self):
        """Create test case setup."""
        self.scanjob = ScanJob(scan_type=ScanTask.SCAN_TYPE_INSPECT)
        self.scanjob.save()

        self.cred = Credential(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred.save()

        self.source = Source(
            name='source1',
            ssh_port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

        self.host = HostRange(host_range='1.2.3.4',
                              source_id=self.source.id)
        self.host.save()

        self.source.hosts.add(self.host)

        scantask = ScanTask(scan_type=ScanTask.SCAN_TYPE_INSPECT,
                            source=self.source, sequence_number=2)
        scantask.save()
        self.scanjob.tasks.add(scantask)

        scantask = ScanTask(scan_type=ScanTask.SCAN_TYPE_INSPECT,
                            source=self.source, sequence_number=1)
        scantask.save()
        self.scanjob.tasks.add(scantask)

        self.scanjob.save()

        self.scanjob.failed_scans = 0
        self.scanjob.save()
        self.fact_endpoint = 'http://testserver' + reverse('facts-list')

        self.scanner = ScanJobRunner(self.scanjob, self.fact_endpoint)

    def test_fake_tasks_success(self):
        """Test success storage."""
        self.scanner.run()
