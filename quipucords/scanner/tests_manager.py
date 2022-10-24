#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the scan manager capabilities."""

from multiprocessing import Process
from unittest.mock import Mock

import pytest

from api.models import ScanTask


class MockTask(Process):
    """Mock Task class."""

    # pylint: disable=invalid-name
    def __init__(self):
        """Create a mock task."""
        super().__init__()
        self.id = 1
        self.scan_job = Mock()
        self.scan_job.status = ScanTask.PENDING
        self.identifier = "TestScan"

    def log_message(self, message):
        """Fake log message."""


class ScanManagerTest:
    """Tests against the Manager class and functions."""

    @pytest.fixture
    def task(self):
        task = MockTask()
        yield task
        if task.is_alive():
            task.kill()

    def test_put(self, task, scan_manager):
        """Test the put feature of the manager."""
        scan_manager.put(task)
        len(scan_manager.scan_queue) == 1

    def test_work(self, task, scan_manager):
        """Test the work function."""
        assert scan_manager.current_job_runner is None
        scan_manager.put(task)
        assert scan_manager.current_job_runner is None
        scan_manager.work()

    def test_kill_missing(self, task, scan_manager):
        """Test kill on missing id."""
        killed = scan_manager.kill(task, "cancel")
        assert killed is False
