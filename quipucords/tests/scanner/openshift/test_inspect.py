"""Test OpenShift InspectTaskRunner."""

import os
from unittest import mock

import pytest
from kubernetes.client import ApiException

from api.models import ScanTask
from constants import DataSources
from quipucords.featureflag import FeatureFlag
from scanner.openshift import InspectTaskRunner, metrics
from scanner.openshift.api import OpenShiftApi
from scanner.openshift.entities import (
    ClusterOperator,
    LifecycleOperator,
    NodeResources,
    OCPCluster,
    OCPError,
    OCPNode,
    OCPWorkload,
)
from tests.factories import ScanTaskFactory


@pytest.fixture
def scan_task():
    """Return a ScanTask for testing."""
    inspect_task = ScanTaskFactory(
        source__source_type=DataSources.OPENSHIFT,
        source__hosts=["1.2.3.4"],
        source__port=4321,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
        sequence_number=1,
    )
    return inspect_task


@pytest.fixture
def operators(faker):
    """Return a list operators."""
    return [
        ClusterOperator(
            name=faker.slug(),
            version="1.2.3",
            created_at=faker.date_time(),
            updated_at=faker.date_time(),
        ),
        LifecycleOperator(
            name=faker.slug(),
            version="3.2.1",
            created_at=faker.date_time(),
            updated_at=faker.date_time(),
        ),
    ]


@pytest.fixture
def workload():
    """Return OCPWorkload entity."""
    return OCPWorkload(name="workload", namespace="project")


@pytest.fixture
def rhacm_metrics():
    """Return list of RHACM metrics."""
    return [
        {
            "vendor": "Openshift",
            "cloud": "Other",
            "version": "1.2.3",
            "managed_cluster_id": "not-a-uuid",
            "available": True,
            "core_worker": 4,
            "socket_worker": 4,
            "created_via": "Other",
        }
    ]


@pytest.fixture
def cluster_metrics(faker):
    """Return a dict that maps each fact name to a list of cluster metrics."""
    fake_host_base = f"cluster-{faker.pyint()}.local"
    return {
        "node_metrics": [
            {
                "instance": f"master-0.{fake_host_base}",
                "label_node_hyperthread_enabled": "true",
                "package": "0",
            },
            {
                "instance": f"master-0.{fake_host_base}",
                "label_node_hyperthread_enabled": "true",
                "package": "1",
            },
            {
                "instance": f"master-1.{fake_host_base}",
                "label_node_hyperthread_enabled": "false",
                "package": "0",
            },
            {
                "instance": f"worker-0.{fake_host_base}",
                "label_node_hyperthread_enabled": "true",
                "package": "0",
            },
            {
                "instance": f"worker-1.{fake_host_base}",
                "label_node_hyperthread_enabled": "false",
                "package": "0",
            },
        ]
    }


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


@pytest.fixture
def workloads_enabled(settings):
    """Set QUIPUCORDS_FEATURE_FLAGS with enabled workloads."""
    with mock.patch.dict(os.environ, {"QUIPUCORDS_FEATURE_OCP_WORKLOADS": "1"}):
        feature_flag = FeatureFlag()
    settings.QUIPUCORDS_FEATURE_FLAGS = feature_flag


@pytest.mark.django_db
@pytest.mark.parametrize(
    "err_status,expected_failed,expected_unreachable",
    [
        (401, 1, 0),
        (999, 0, 1),
    ],
)
def test_connect_with_error(
    mocker, err_status, expected_failed, expected_unreachable, scan_task: ScanTask
):
    """Test connecting to OpenShift host with failure."""
    error = OCPError(status=err_status, reason="fail", message="fail")
    mocker.patch.object(OpenShiftApi, "can_connect", side_effect=error)
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task()
    assert message == InspectTaskRunner.FAILURE_TO_CONNECT_MESSAGE
    assert status == ScanTask.FAILED
    assert scan_task.systems_count == 1
    assert scan_task.systems_scanned == 0
    assert scan_task.systems_failed == expected_failed
    assert scan_task.systems_unreachable == expected_unreachable


@pytest.mark.django_db
def test_inspect_with_success(  # noqa: PLR0913
    mocker,
    scan_task: ScanTask,
    cluster,
    node_ok,
    operators,
    rhacm_metrics,
):
    """Test inspecting OpenShift host with success."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster)
    mocker.patch.object(OpenShiftApi, "retrieve_nodes", return_value=[node_ok])
    mocker.patch.object(OpenShiftApi, "retrieve_operators", return_value=operators)
    mocker.patch.object(
        OpenShiftApi, "retrieve_rhacm_metrics", return_value=rhacm_metrics
    )
    mocker.patch.object(metrics, "retrieve_cluster_metrics", return_value=[])

    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task()
    assert message == InspectTaskRunner.SUCCESS_MESSAGE
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 2
    assert scan_task.systems_scanned == 2
    assert scan_task.systems_failed == 0
    assert scan_task.systems_unreachable == 0


@pytest.mark.django_db
def test_inspect_with_success_cluster_metrics(  # noqa: PLR0913
    mocker,
    scan_task: ScanTask,
    cluster,
    node_ok,
    operators,
    rhacm_metrics,
    cluster_metrics,
):
    """Test inspecting OpenShift host and successfully retrieving cluster metrics."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster)
    mocker.patch.object(OpenShiftApi, "retrieve_nodes", return_value=[node_ok])
    mocker.patch.object(OpenShiftApi, "retrieve_operators", return_value=operators)
    mocker.patch.object(
        OpenShiftApi, "retrieve_rhacm_metrics", return_value=rhacm_metrics
    )

    def retrieve_cluster_metrics(ocp_client, metric):
        for metric_name, reference_metric in metrics.OCP_PROMETHEUS_METRICS.items():
            if metric == reference_metric:
                return cluster_metrics[metric_name]
        raise NotImplementedError

    mocker.patch.object(
        metrics, "retrieve_cluster_metrics", side_effect=retrieve_cluster_metrics
    )
    # Note: We use this side_effect function for retrieve_cluster_metrics because it can
    # be called multiple times, even though currently in practice we only call it once.

    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task()
    assert message == InspectTaskRunner.SUCCESS_MESSAGE
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 2
    assert scan_task.systems_scanned == 2
    assert scan_task.systems_failed == 0
    assert scan_task.systems_unreachable == 0

    metrics.retrieve_cluster_metrics.assert_called_once()
    extra_facts = [fact for fact in scan_task.get_facts() if "node_metrics" in fact]
    assert len(extra_facts) == 1
    assert extra_facts[0]["node_metrics"] == cluster_metrics["node_metrics"]


@pytest.mark.django_db
def test_inspect_with_partial_success(  # noqa: PLR0913
    mocker,
    scan_task: ScanTask,
    cluster,
    node_ok,
    node_err,
    operators,
    rhacm_metrics,
):
    """Test connecting to OpenShift host with success."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster)
    mocker.patch.object(metrics, "retrieve_cluster_metrics", return_value=[])
    mocker.patch.object(
        OpenShiftApi, "retrieve_nodes", return_value=[node_ok, node_err]
    )
    mocker.patch.object(OpenShiftApi, "retrieve_operators", return_value=operators)
    mocker.patch.object(
        OpenShiftApi, "retrieve_rhacm_metrics", return_value=rhacm_metrics
    )

    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task()
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
    cluster_err,
    node_err,
    operators,
    rhacm_metrics,
):
    """Test connecting to OpenShift host with success."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster_err)
    mocker.patch.object(OpenShiftApi, "retrieve_nodes", return_value=[node_err])
    mocker.patch.object(OpenShiftApi, "retrieve_operators", return_value=operators)
    mocker.patch.object(
        OpenShiftApi, "retrieve_rhacm_metrics", return_value=rhacm_metrics
    )
    mocker.patch.object(metrics, "retrieve_cluster_metrics", return_value=[])

    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    message, status = runner.execute_task()
    assert message == InspectTaskRunner.FAILURE_MESSAGE
    assert status == ScanTask.FAILED
    assert scan_task.systems_count == 2
    assert scan_task.systems_scanned == 0
    assert scan_task.systems_failed == 2
    assert scan_task.systems_unreachable == 0


EXTRA_CLUSTER_FACTS = {"operators", "workloads", "rhacm_metrics"}


@pytest.mark.django_db
@pytest.mark.parametrize("extra_fact_with_error", sorted(EXTRA_CLUSTER_FACTS))
def test_inspect_errors_on_extra_cluster_facts(  # noqa: PLR0913
    mocker,
    scan_task: ScanTask,
    cluster,
    node_ok,
    extra_fact_with_error,
    workloads_enabled,
):
    """Test connecting to OpenShift host with errors collecting extra cluster facts."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster)
    mocker.patch.object(OpenShiftApi, "retrieve_nodes", return_value=[node_ok])
    mocker.patch.object(metrics, "retrieve_cluster_metrics", return_value=[])
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
    message, status = runner.execute_task()
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


@pytest.mark.django_db
def test_inspect_with_enabled_workloads(  # noqa: PLR0913
    mocker,
    scan_task: ScanTask,
    cluster,
    node_ok,
    workload,
    operators,
    workloads_enabled,
    rhacm_metrics,
):
    """Test connecting to OpenShift host with enabled workloads."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster)
    mocker.patch.object(OpenShiftApi, "retrieve_nodes", return_value=[node_ok])
    mocker.patch.object(OpenShiftApi, "retrieve_workloads", return_value=[workload])
    mocker.patch.object(OpenShiftApi, "retrieve_operators", return_value=operators)
    mocker.patch.object(
        OpenShiftApi, "retrieve_rhacm_metrics", return_value=rhacm_metrics
    )
    mocker.patch.object(metrics, "retrieve_cluster_metrics", return_value=[])

    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.execute_task()

    raw_facts = scan_task.get_facts()
    cluster = raw_facts[-1]
    assert "workloads" in cluster.keys()


@pytest.mark.django_db
def test_inspect_with_disabled_workloads(  # noqa: PLR0913
    mocker, scan_task: ScanTask, cluster, node_ok, operators, rhacm_metrics
):
    """Test connecting to OpenShift host with workloads default behavior."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    mocker.patch.object(OpenShiftApi, "retrieve_cluster", return_value=cluster)
    mocker.patch.object(OpenShiftApi, "retrieve_nodes", return_value=[node_ok])
    mocker.patch.object(OpenShiftApi, "retrieve_operators", return_value=operators)
    mocker.patch.object(metrics, "retrieve_cluster_metrics", return_value=[])
    mock_retrieve_workloads = mocker.patch.object(
        OpenShiftApi, "retrieve_workloads", return_value=[workload]
    )
    mocker.patch.object(
        OpenShiftApi, "retrieve_rhacm_metrics", return_value=rhacm_metrics
    )

    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.execute_task()

    mock_retrieve_workloads.assert_not_called()
    raw_facts = scan_task.get_facts()
    cluster = raw_facts[-1]
    assert "workloads" not in cluster.keys()
    assert set(("cluster", "operators")).issubset(cluster.keys())
