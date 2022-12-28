# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test OpenShift InspectTaskRunner."""

import pytest

from api.models import ScanTask, Source
from scanner.exceptions import ScanFailureError
from scanner.openshift import InspectTaskRunner
from scanner.openshift.api import OpenShiftApi
from scanner.openshift.entities import OCPDeployment, OCPError, OCPProject
from tests.factories import ScanTaskFactory


@pytest.fixture
def scan_task():
    """Return a ScanTask for testing."""
    connect_task = ScanTaskFactory(
        source__source_type=Source.OPENSHIFT_SOURCE_TYPE,
        source__hosts='["1.2.3.4"]',
        source__port=4321,
        scan_type=ScanTask.SCAN_TYPE_CONNECT,
        status=ScanTask.COMPLETED,
        sequence_number=1,
    )
    inspect_task = ScanTaskFactory(
        source=connect_task.source,
        job=connect_task.job,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
    )
    inspect_task.prerequisites.add(connect_task)
    return inspect_task


@pytest.fixture
def project_ok():
    """Return OCPProject entity."""
    return OCPProject(name="project-ok", labels={"project": "ok"})


@pytest.fixture
def project_err():
    """Return OCPProject entity."""
    return OCPProject(name="project-err", labels={"project": "err"})


@pytest.fixture
def deployment():
    """Return OCPDeployment entity."""
    return OCPDeployment(
        name="deployment-name",
        labels={"deployment": "label"},
        container_images=["some-image"],
        init_container_images=[],
    )


@pytest.fixture
def error():
    """Return OCPError entity."""
    return OCPError(status=500, reason="error-reason", message="error-message")


@pytest.fixture(autouse=True)
def _patched_retrieve_deployments(mocker, error, deployment):
    """Mock OpenShiftApi retrieve_deployments method to return our fixtures."""

    def _retrieve(project_name, **kwargs):
        if project_name == "project-ok":
            return deployment
        if project_name == "project-err":
            raise error
        raise NotImplementedError()

    mocker.patch.object(OpenShiftApi, "retrieve_deployments", side_effect=_retrieve)


@pytest.mark.django_db
def test_inspect_prerequisite_failure(mocker, scan_task: ScanTask):
    """Test Inspect scan prerequisite failure."""
    conn_task = scan_task.prerequisites.first()
    conn_task.status = ScanTask.FAILED
    conn_task.save()

    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    with pytest.raises(ScanFailureError, match="Prerequisite scan have failed."):
        runner.execute_task(mocker.Mock())


@pytest.mark.django_db
def test_inspect_with_success(mocker, scan_task: ScanTask, project_ok):
    """Test connecting to OpenShift host with success."""
    mocker.patch.object(OpenShiftApi, "retrieve_projects", return_value=[project_ok])
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task(mocker.Mock())
    assert message == InspectTaskRunner.SUCCESS_MESSAGE
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 1
    assert scan_task.systems_scanned == 1
    assert scan_task.systems_failed == 0
    assert scan_task.systems_unreachable == 0


@pytest.mark.django_db
def test_inspect_with_partial_success(
    mocker, scan_task: ScanTask, project_ok, project_err
):
    """Test connecting to OpenShift host with success."""
    mocker.patch.object(
        OpenShiftApi, "retrieve_projects", return_value=[project_ok, project_err]
    )
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task(mocker.Mock())
    assert message == InspectTaskRunner.PARTIAL_SUCCESS_MESSAGE
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 2
    assert scan_task.systems_scanned == 1
    assert scan_task.systems_failed == 1
    assert scan_task.systems_unreachable == 0


@pytest.mark.django_db
def test_inspect_with_failure(mocker, scan_task: ScanTask, project_err):
    """Test connecting to OpenShift host with success."""
    mocker.patch.object(OpenShiftApi, "retrieve_projects", return_value=[project_err])
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task(mocker.Mock())
    assert message == InspectTaskRunner.FAILURE_MESSAGE
    assert status == ScanTask.FAILED
    assert scan_task.systems_count == 1
    assert scan_task.systems_scanned == 0
    assert scan_task.systems_failed == 1
    assert scan_task.systems_unreachable == 0
