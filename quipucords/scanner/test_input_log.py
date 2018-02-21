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
import unittest
from unittest import mock

from django.test import TestCase

from scanner import input_log


class TestDatabaseUUID(TestCase):
    """Test get_sonar_uuid()."""

    def test_uuid(self):
        """Get UUID three times, verify stability."""
        # First retrieval makes new uuid
        uuid_1 = input_log.get_database_uuid()
        self.assertIsInstance(uuid_1, uuid.UUID)

        # Next retrievals should return the same object
        self.assertEqual(input_log.get_database_uuid(), uuid_1)
        self.assertEqual(input_log.get_database_uuid(), uuid_1)


class TestNextSequenceNumber(TestCase):
    """Test next_sequence_number()."""

    def test_next_sequence_number(self):
        """Get next_sequence_number() three times."""
        # First retrieval starts at 0
        self.assertEqual(input_log.next_sequence_number(), 0)

        # Next retrievals count up
        self.assertEqual(input_log.next_sequence_number(), 1)
        self.assertEqual(input_log.next_sequence_number(), 2)


class TestRotatingLogFile(unittest.TestCase):
    """Test RotatingLogFile."""

    def test_rotating_log_file(self):
        """Make a RotatingLogFile and walk through basic usage."""
        rlf = input_log.RotatingLogFile(100, 100, dry_run=True)

        self.assertEqual(rlf.step_size, 10)
        self.assertEqual(rlf.step_age, 10)

        base_2 = ('base-2', mock.Mock(st_ctime=1, st_size=1))
        base_3 = ('base-3', mock.Mock(st_ctime=2, st_size=1))
        base_4 = ('base-4', mock.Mock(st_ctime=3, st_size=1))

        rlf.basename = 'base'
        rlf.dirname = ''
        rlf.read_files_from_stats([base_2, base_3, base_4])

        self.assertEqual(rlf.log_files,
                         [{'name': 'base-4', 'created': 3, 'size': 1},
                          {'name': 'base-3', 'created': 2, 'size': 1},
                          {'name': 'base-2', 'created': 1, 'size': 1}])
        self.assertEqual(rlf.file_counter, 4)

        # 'foo' will fit in log file 'base-4'
        rlf.write_record('foo', now=4)
        self.assertEqual(rlf.file_counter, 4)
        self.assertEqual(rlf.log_files[0]['name'], 'base-4')

        # 'thisisalongrecord' will trigger creation of 'base-5'
        rlf.write_record('thisisalongrecord', now=5)
        self.assertEqual(rlf.file_counter, 5)
        self.assertEqual(rlf.log_files[0]['name'], 'base-5')
