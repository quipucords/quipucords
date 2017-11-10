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
"""Test the scan manager capabilities."""

from threading import Thread
from django.test import TestCase
from scanner.manager import Manager


class MockTask(Thread):
    """Mock Task class."""

    def __init__(self):
        """Create a mock task."""
        Thread.__init__(self)
        self.identifier = 1


class ScanManagerTest(TestCase):
    """Tests against the Manager class and functions."""

    scan_manager = None

    def setUp(self):
        """Create test case setup."""
        self.scan_manager = Manager()
        self.scan_manager.start()

    def tearDown(self):
        """Cleanup test case setup."""
        if self.scan_manager.is_alive():
            self.scan_manager.running = False
            self.scan_manager.join()

    def test_put(self):
        """Test the put feature of the manager."""
        task = MockTask()
        self.scan_manager.put(task)
        self.assertEqual(len(self.scan_manager.scan_queue), 1)

    def test_work(self):
        """Test the work function."""
        task = MockTask()
        self.scan_manager.put(task)
        self.scan_manager.work()
        self.assertIsNone(self.scan_manager.current_task)

    def test_kill_missing(self):
        """Test kill on missing id."""
        killed = self.scan_manager.kill(1)
        self.assertFalse(killed)

    def test_kill(self):
        """Test kill on added task."""
        task = MockTask()
        self.scan_manager.put(task)
        killed = self.scan_manager.kill(1)
        self.assertTrue(killed)
