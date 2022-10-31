# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test OpenShift ConnectTaskRunner."""

import pytest

from api.models import ScanTask, Source
from scanner.openshift import ConnectTaskRunner
from scanner.openshift.api import OpenShiftApi
from scanner.openshift.entities import OCPError
from tests.factories import ScanTaskFactory


@pytest.fixture(autouse=True)
def _patch_scan_manager(disabled_scan_manager):
    """Disable automatic spawned scan manager."""


@pytest.fixture
def scan_task():
    """Return a ScanTask for testing."""
    return ScanTaskFactory(
        source__source_type=Source.OPENSHIFT_SOURCE_TYPE,
        source__hosts='["1.2.3.4"]',
        source__port=4321,
        scan_type=ScanTask.SCAN_TYPE_CONNECT,
    )


@pytest.mark.django_db
def test_connect_with_success(mocker, scan_task: ScanTask):
    """Test connecting to OpenShift host with success."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    runner = ConnectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task(mocker.Mock())
    assert message == ConnectTaskRunner.SUCCESS_MESSAGE
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 1
    assert scan_task.systems_scanned == 1
    assert scan_task.systems_failed == 0
    assert scan_task.systems_unreachable == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "err_status,expected_failed,expected_ureachable",
    [
        (401, 1, 0),
        (999, 0, 1),
    ],
)
def test_connect_with_error(
    mocker, err_status, expected_failed, expected_ureachable, scan_task: ScanTask
):
    """Test connecting to OpenShift host with failure."""
    error = OCPError(status=err_status, reason="fail", message="fail")
    mocker.patch.object(OpenShiftApi, "can_connect", side_effect=error)
    runner = ConnectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task(mocker.Mock())
    assert message == ConnectTaskRunner.FAILURE_MESSAGE
    assert status == ScanTask.FAILED
    assert scan_task.systems_count == 1
    assert scan_task.systems_scanned == 0
    assert scan_task.systems_failed == expected_failed
    assert scan_task.systems_unreachable == expected_ureachable
