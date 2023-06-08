"""Test OpenShift InspectTaskRunner."""

import pytest
from kubernetes.client import ApiException

from api.models import ScanTask
from constants import DataSources
from scanner.exceptions import ScanFailureError
from scanner.openshift import InspectTaskRunner
from scanner.openshift.api import OpenShiftApi
from scanner.openshift.entities import (
    NodeResources,
    OCPCluster,
    OCPError,
    OCPNode,
    OCPProject,
    OCPWorkload,
)
from tests.factories import ScanTaskFactory


@pytest.fixture
def scan_task():
    """Return a ScanTask for testing."""
    connect_task = ScanTaskFactory(
        source__source_type=DataSources.OPENSHIFT,
        source__hosts=["1.2.3.4"],
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
def project():
    """Return OCPProject entity."""
    return OCPProject(name="project", labels={"project": "ok"})


@pytest.fixture
def workload():
    """Return OCPWorkload entity."""
    return OCPWorkload(name="workload", namespace="project")


@pytest.fixture
def node_resources():
    """Return Node Resources entity."""
    return NodeResources(cpu="350m", memory_in_bytes="15252796Ki", pods="250")


@pytest.fixture
def error():
    """Return OCPError entity."""
    return OCPError(status=500, reason="error-reason", message="error-message")


@pytest.fixture
def node_ok(node_resources):
    """Return OCPNode entity."""
    return OCPNode(
        name="node-ok",
        creation_timestamp="2022-12-18T03:56:20Z",
        labels={"_ok": "label"},
        addresses=[{"ip_1": "4.3.2.1"}, {"ip_2": "1.2.3.4"}],
        allocatable=node_resources,
        capacity=node_resources,
        architecture="arch",
        kernel_version="node_kernel_version",
        machine_id="12345",
        operating_system="linux",
        taints=[{"effect": "_ok-effect", "key": "master"}],
    )


@pytest.fixture
def node_err(error):
    """Return OCPNode entity with error."""
    return OCPNode(
        name="node-err", labels={"project": "err"}, errors={"error": error.dict()}
    )


@pytest.fixture
def cluster():
    """Return OCPCluster."""
    return OCPCluster(uuid="not-a-uuid", version="1.2.3.4")


@pytest.fixture
def cluster_err(error):
    """Return OCPCluster with associated error."""
    return OCPCluster(uuid="yet-another-not-uuid", errors={"some-error": error.dict()})


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
def test_inspect_with_success(  # noqa: PLR0913
    mocker, scan_task: ScanTask, project, cluster, node_ok, workload
):
    """Test connecting to OpenShift host with success."""
    mocker.patch.object(OpenShiftApi, "retrieve_projects", return_value=[project])
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster)
    mocker.patch.object(OpenShiftApi, "retrieve_nodes", return_value=[node_ok])
    mocker.patch.object(OpenShiftApi, "retrieve_workloads", return_value=[workload])

    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task(mocker.Mock())
    assert message == InspectTaskRunner.SUCCESS_MESSAGE
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 2
    assert scan_task.systems_scanned == 2
    assert scan_task.systems_failed == 0
    assert scan_task.systems_unreachable == 0


@pytest.mark.django_db
def test_inspect_with_partial_success(  # noqa: PLR0913
    mocker,
    scan_task: ScanTask,
    project,
    cluster,
    node_ok,
    node_err,
    workload,
):
    """Test connecting to OpenShift host with success."""
    mocker.patch.object(OpenShiftApi, "retrieve_projects", return_value=[project])
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster)
    mocker.patch.object(
        OpenShiftApi, "retrieve_nodes", return_value=[node_ok, node_err]
    )
    mocker.patch.object(OpenShiftApi, "retrieve_workloads", return_value=[workload])

    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task(mocker.Mock())
    assert message == InspectTaskRunner.PARTIAL_SUCCESS_MESSAGE
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 3
    assert scan_task.systems_scanned == 2
    assert scan_task.systems_failed == 1
    assert scan_task.systems_unreachable == 0


@pytest.mark.django_db
def test_inspect_with_failure(  # noqa: PLR0913
    mocker,
    scan_task: ScanTask,
    project,
    cluster_err,
    node_err,
    workload,
):
    """Test connecting to OpenShift host with success."""
    mocker.patch.object(OpenShiftApi, "retrieve_projects", return_value=[project])
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster_err)
    mocker.patch.object(OpenShiftApi, "retrieve_nodes", return_value=[node_err])
    mocker.patch.object(OpenShiftApi, "retrieve_workloads", return_value=[workload])
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task(mocker.Mock())
    assert message == InspectTaskRunner.FAILURE_MESSAGE
    assert status == ScanTask.FAILED
    assert scan_task.systems_count == 2
    assert scan_task.systems_scanned == 0
    assert scan_task.systems_failed == 2
    assert scan_task.systems_unreachable == 0


EXTRA_CLUSTER_FACTS = {"projects", "workloads"}


@pytest.mark.django_db
@pytest.mark.parametrize("extra_fact_with_error", sorted(EXTRA_CLUSTER_FACTS))
def test_inspect_errors_on_extra_cluster_facts(
    mocker,
    scan_task: ScanTask,
    cluster,
    node_ok,
    extra_fact_with_error,
):
    """Test connecting to OpenShift host with errors collecting extra cluster facts."""
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster)
    mocker.patch.object(OpenShiftApi, "retrieve_nodes", return_value=[node_ok])
    # leave non-error extra facts empty (since this won't be considered an error and is
    # easier to test)
    for extra_fact in EXTRA_CLUSTER_FACTS - {extra_fact_with_error}:
        mocker.patch.object(OpenShiftApi, f"retrieve_{extra_fact}", return_value=[])
    teapot_response = mocker.Mock(status=418, reason="🫖", data=b"I'm a teapot")
    # simulate an OCP API error for the collection of 'fact with error'
    teapot_exc = OCPError.from_api_exception(ApiException(http_resp=teapot_response))
    mocker.patch.object(
        OpenShiftApi,
        f"retrieve_{extra_fact_with_error}",
        side_effect=teapot_exc,
    )
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task(mocker.Mock())
    assert message == InspectTaskRunner.PARTIAL_SUCCESS_MESSAGE
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 2
    assert scan_task.systems_scanned == 1
    assert scan_task.systems_failed == 1
    assert scan_task.systems_unreachable == 0

    raw_facts = scan_task.get_facts()
    # sanity check cluster fact
    cluster = raw_facts[-1]
    assert isinstance(cluster, dict)
    assert "cluster" in cluster.keys()
    # check errors
    assert cluster["cluster"]["errors"] == {
        extra_fact_with_error: {
            "kind": "error",
            "status": teapot_response.status,
            "reason": teapot_response.reason,
            "message": teapot_response.data.decode(),
        }
    }
