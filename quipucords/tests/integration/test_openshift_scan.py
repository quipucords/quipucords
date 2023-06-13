"""Integration test for OpenShift scan."""

import json
from logging import getLogger

import pytest

from api.inspectresult.model import RawFactEncoder
from constants import DataSources
from scanner.openshift.api import OpenShiftApi
from scanner.openshift.entities import (
    ClusterOperator,
    LifecycleOperator,
    NodeResources,
    OCPCluster,
    OCPNode,
    OCPProject,
    OCPWorkload,
)
from tests.integration.test_smoker import Smoker

logger = getLogger(__name__)


@pytest.fixture
def expected_middleware_names():
    """Middleware names."""
    return {}


@pytest.fixture
def fingerprint_fact_map():
    """Map fingerprint to raw fact name."""
    return {
        "architecture": "node__architecture",
        "cpu_count": "node__capacity__cpu",
        "etc_machine_id": "node__machine_id",
        "ip_addresses": "node__addresses",
        "name": "node__name",
        "system_creation_date": "node__creation_timestamp",
        "system_role": "node__labels",
        "vm_cluster": "node__cluster_uuid",
    }


@pytest.fixture
def node_resources():
    """Return a NodeResources instance."""
    return NodeResources(cpu="4", memory_in_bytes="15252796Ki", pods="250")


@pytest.fixture
def expected_node(node_resources):
    """Return a OCPNode."""
    return OCPNode(
        name="node name",
        errors={},
        labels={"node-role.kubernetes.io/master": ""},
        taints=[{"key": "some", "effect": "some"}],
        capacity=node_resources,
        addresses=[{"type": "ip", "address": "1.2.3.4"}],
        machine_id="<MACHINE-ID>",
        allocatable=node_resources,
        architecture="amd64",
        kernel_version="4.18.0-305.65.1.el8_4.x86_64",
        operating_system="linux",
        creation_timestamp="2022-12-18T03:56:20Z",
    )


@pytest.fixture
def expected_cluster():
    """Return an OCP cluster."""
    return OCPCluster(
        uuid="<CLUSTER-UUID>",
        version="4.10",
    )


@pytest.fixture
def expected_projects():
    """Return a list with OCP projects."""
    return [
        OCPProject(
            name="project name",
            labels={"some": "label"},
        ),
    ]


@pytest.fixture
def expected_operators(faker):
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
def expected_workloads():
    """Return a list of OCP workloads."""
    return [OCPWorkload(name="workload-name", container_images=["some-image"])]


def _formatter(entity):
    """Format OCP entities as they should appear on details report."""
    encoded_data = json.dumps(entity, cls=RawFactEncoder)
    return json.loads(encoded_data)


@pytest.fixture
def expected_facts(
    expected_projects,
    expected_node,
    expected_cluster,
    expected_workloads,
    expected_operators,
):
    """Return a list of expected raw facts on OCP scans."""
    expected_node.cluster_uuid = expected_cluster.uuid
    return [
        {"node": _formatter(expected_node)},
        {
            "cluster": _formatter(expected_cluster),
            "projects": _formatter(expected_projects),
            "workloads": _formatter(expected_workloads),
            "operators": _formatter(expected_operators),
        },
    ]


@pytest.fixture(autouse=True)
def patched_openshift_client(  # noqa: PLR0913
    mocker,
    expected_projects,
    expected_node,
    expected_cluster,
    expected_workloads,
    expected_operators,
):
    """Mock OpenShiftApi forcing it to return expected entities."""
    mocker.patch.object(OpenShiftApi, "can_connect", return_value=True)
    mocker.patch.object(
        OpenShiftApi,
        "retrieve_projects",
        return_value=expected_projects,
    )
    mocker.patch.object(
        OpenShiftApi,
        "retrieve_nodes",
        return_value=[expected_node],
    )
    mocker.patch.object(
        OpenShiftApi,
        "retrieve_cluster",
        return_value=expected_cluster,
    )
    mocker.patch.object(
        OpenShiftApi,
        "retrieve_workloads",
        return_value=expected_workloads,
    )
    mocker.patch.object(
        OpenShiftApi,
        "retrieve_operators",
        return_value=expected_operators,
    )


@pytest.mark.integration
@pytest.mark.django_db
class TestOpenShiftScan(Smoker):
    """Smoke test OpenShift scan."""

    MAX_RETRIES = 10
    SOURCE_NAME = "testing source"
    SOURCE_TYPE = DataSources.OPENSHIFT

    @pytest.fixture
    def credential_payload(self):
        """Return OCP credential payload."""
        return {
            "name": "testing credential",
            "auth_token": "<TOKEN>",
        }

    @pytest.fixture
    def source_payload(self):
        """Return OCP source payload."""
        return {
            "source_type": self.SOURCE_TYPE,
            "hosts": ["ocp.host"],
            "port": 7891,
        }

    @pytest.fixture
    def expected_fingerprints(self):
        """Return expected fingerprint values."""
        return {
            "architecture": "x86_64",
            "system_role": "master",
            "vm_cluster": "<CLUSTER-UUID>",
        }
