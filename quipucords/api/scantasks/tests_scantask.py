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
"""Test the API application."""

from django.test import TestCase
from api.models import Credential, Source, ScanTask
from api.serializers import ScanTaskSerializer


def dummy_start():
    """Create a dummy method for testing."""
    pass


# pylint: disable=unused-argument
class ScanTaskTest(TestCase):
    """Test the basic ScanJob infrastructure."""

    def setUp(self):
        """Create test setup."""
        self.cred = Credential.objects.create(
            name='cred1',
            username='username',
            password='password',
            sudo_password=None,
            ssh_keyfile=None)
        self.cred_for_upload = self.cred.id

        self.source = Source(
            name='source1',
            source_type='network',
            ssh_port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

    def test_successful_create(self):
        """Create a scan task and serialize it."""
        task = ScanTask.objects.create(
            source=self.source,
            scan_type=ScanTask.DISCOVERY,
            status=ScanTask.PENDING)
        serializer = ScanTaskSerializer(task)
        json_task = serializer.data
        self.assertEqual(
            {'id': 1,
             'source': 1,
             'scan_type': 'discovery',
             'status': 'pending'},
            json_task)
