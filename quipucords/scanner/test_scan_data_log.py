# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test the input logger."""

import uuid

from django.test import TestCase

from scanner import scan_data_log


class TestDatabaseUUID(TestCase):
    """Test get_sonar_uuid()."""

    def test_uuid(self):
        """Get UUID three times, verify stability."""
        # First retrieval makes new uuid
        uuid_1 = scan_data_log.get_database_uuid()
        self.assertIsInstance(uuid_1, uuid.UUID)

        # Next retrievals should return the same object
        self.assertEqual(scan_data_log.get_database_uuid(), uuid_1)
        self.assertEqual(scan_data_log.get_database_uuid(), uuid_1)


class TestNextSequenceNumber(TestCase):
    """Test next_sequence_number()."""

    def test_next_sequence_number(self):
        """Get next_sequence_number() three times."""
        # First retrieval starts at 0
        self.assertEqual(scan_data_log.next_sequence_number(), 0)

        # Next retrievals count up
        self.assertEqual(scan_data_log.next_sequence_number(), 1)
        self.assertEqual(scan_data_log.next_sequence_number(), 2)
