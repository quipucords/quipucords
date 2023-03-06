"""Integration test for OpenShift scan."""

import tarfile
from io import BytesIO
from logging import getLogger
from time import sleep
from unittest import mock

import pytest

from api.models import ScanTask
from fingerprinter.constants import (
    ENTITLEMENTS_KEY,
    META_DATA_KEY,
    PRODUCTS_KEY,
    SOURCES_KEY,
)
from scanner.openshift.api import OpenShiftApi
from scanner.openshift.entities import (
    NodeResources,
    OCPCluster,
    OCPNode,
    OCPProject,
    OCPWorkload,
)
from tests.utils.facts import RawFactComparator
from utils import load_json_from_tarball

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
    """Return a list with OCP node."""
    return [
        OCPNode(
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
    ]


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
def expected_workloads():
    """Return a list of OCP workloads."""
    return [OCPWorkload(name="workload-name", container_images=["some-image"])]


@pytest.fixture
def expected_facts(
    expected_projects, expected_node, expected_cluster, expected_workloads
):
    """Return a list of expected raw facts on OCP scans."""
    projects_list = [p.dict() for p in expected_projects]
    _node = expected_node[0].dict()
    _node["creation_timestamp"] = _node["creation_timestamp"].isoformat()
    _node["cluster_uuid"] = expected_cluster.uuid
    return [
        {"node": _node},
        {
            "cluster": expected_cluster.dict(),
            "projects": projects_list,
            "workloads": expected_workloads,
        },
    ]


@pytest.fixture(autouse=True)
def patched_openshift_client(
    mocker, expected_projects, expected_node, expected_cluster, expected_workloads
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
        return_value=expected_node,
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


@pytest.mark.integration
@pytest.mark.django_db
class TestOpenShiftScan:
    """Smoke test OpenShift scan."""

    MAX_RETRIES = 10
    SOURCE_NAME = "testing source"
    SOURCE_TYPE = "openshift"

    @pytest.fixture
    def credential_id(self, django_client):
        """Create ocp credentials through api and return credentials identifier."""
        response = django_client.post(
            "credentials/",
            json={
                "name": "testing credential",
                "cred_type": self.SOURCE_TYPE,
                "auth_token": "<TOKEN>",
            },
        )
        assert response.ok, response.text
        return response.json()["id"]

    @pytest.fixture
    def source_id(self, django_client, credential_id):
        """Register source for ocp scan through api and return its identifier."""
        response = django_client.post(
            "sources/",
            json={
                "source_type": self.SOURCE_TYPE,
                "credentials": [credential_id],
                "hosts": ["ocp.host"],
                "name": self.SOURCE_NAME,
                "port": 7891,
            },
        )
        assert response.ok, response.text
        return response.json()["id"]

    @pytest.fixture
    def scan_id(self, django_client, source_id):
        """Create a scan and return its identifier."""
        create_scan_response = django_client.post(
            "scans/",
            json={"name": "test scan", "sources": [source_id]},
        )
        assert create_scan_response.ok, create_scan_response.text
        scan_id = create_scan_response.json()["id"]
        return scan_id

    @pytest.fixture
    def scan_response(self, django_client, scan_id, scan_manager):
        """Start a scan job and poll its results endpoint until completion."""
        create_scan_job_response = django_client.post(f"scans/{scan_id}/jobs/")
        assert create_scan_job_response.ok, create_scan_job_response.text
        scan_manager.work()
        response = django_client.get(f"scans/{scan_id}/")
        attempts = 1
        assert response.ok, response.text

        completed_status = {ScanTask.COMPLETED, ScanTask.CANCELED, ScanTask.FAILED}
        while (
            scan_status := response.json()["most_recent"]["status"]
        ) not in completed_status and attempts < self.MAX_RETRIES:
            attempts += 1
            backoff = 2**attempts
            sleep(backoff)
            response = django_client.get(f"scans/{scan_id}/")
            assert response.ok, response.text

        assert scan_status == ScanTask.COMPLETED, response.json()

        return response

    @pytest.fixture
    def report_id(self, scan_response):
        """Return the latest report id from performed scan."""
        return scan_response.json()["most_recent"]["report_id"]

    def test_details_report(
        self,
        django_client,
        report_id,
        expected_facts,
    ):
        """Sanity check details report."""
        response = django_client.get(f"reports/{report_id}/details/")
        assert response.ok, response.text
        report_details_dict = response.json()
        expected_details_report = {
            "report_id": report_id,
            "report_platform_id": mock.ANY,
            "report_type": "details",
            "report_version": mock.ANY,
            SOURCES_KEY: [
                {
                    "facts": mock.ANY,
                    "report_version": mock.ANY,
                    "server_id": mock.ANY,
                    "source_name": self.SOURCE_NAME,
                    "source_type": self.SOURCE_TYPE,
                }
            ],
        }
        assert report_details_dict == expected_details_report
        report_details_facts = report_details_dict[SOURCES_KEY][0]["facts"]
        assert report_details_facts == expected_facts

    @pytest.fixture
    def expected_fingerprint_metadata(self, fingerprint_fact_map):
        """
        Return expected metadata dictionary.

        Dict contained within deployments report > system fingerprints.
        """
        metadata = {}
        for fingerprint_fact, raw_fact in fingerprint_fact_map.items():
            metadata[fingerprint_fact] = {
                "server_id": mock.ANY,
                "source_name": self.SOURCE_NAME,
                "source_type": self.SOURCE_TYPE,
                "raw_fact_key": RawFactComparator(raw_fact),
                "has_sudo": False,
            }
        return metadata

    def test_deployments_report(
        self,
        django_client,
        expected_fingerprint_metadata,
        fingerprint_fact_map,
        report_id,
    ):
        """Sanity check report deployments json structure."""
        response = django_client.get(f"reports/{report_id}/deployments/")
        assert response.ok, response.json()

        report_deployments_dict = response.json()
        assert report_deployments_dict == {
            "report_id": report_id,
            "status": ScanTask.COMPLETED,
            "report_type": "deployments",
            "report_version": mock.ANY,
            "report_platform_id": mock.ANY,
            "system_fingerprints": [mock.ANY],
        }

        fingerprints_dict = report_deployments_dict["system_fingerprints"][0]
        fingerprint_fact_names = set(fingerprints_dict[META_DATA_KEY].keys())
        assert fingerprint_fact_names == set(fingerprint_fact_map.keys())
        assert fingerprints_dict == {
            "id": mock.ANY,
            "deployment_report": mock.ANY,
            ENTITLEMENTS_KEY: [],
            SOURCES_KEY: [
                {
                    "server_id": mock.ANY,
                    "source_name": self.SOURCE_NAME,
                    "source_type": self.SOURCE_TYPE,
                }
            ],
            PRODUCTS_KEY: [],
            META_DATA_KEY: mock.ANY,
            **{fingerprint: mock.ANY for fingerprint in fingerprint_fact_map.keys()},
        }
        assert fingerprints_dict[META_DATA_KEY] == expected_fingerprint_metadata
        assert fingerprints_dict["architecture"] == "x86_64"
        assert fingerprints_dict["system_role"] == "master"
        assert fingerprints_dict["vm_cluster"] == "<CLUSTER-UUID>"

    def test_compare_standalone_json_reports_with_tarball(
        self, django_client, report_id
    ):
        """Compare individual reports with the ones bundled on the tarball endpoint."""
        details_response = django_client.get(f"reports/{report_id}/details/")
        assert details_response.ok, details_response.json()

        deployments_response = django_client.get(f"reports/{report_id}/deployments/")
        assert deployments_response.ok, deployments_response.json()

        full_report_response = django_client.get(f"reports/{report_id}/")
        assert full_report_response.ok

        with tarfile.open(fileobj=BytesIO(full_report_response.content)) as tarball:
            tarball_details_dict = load_json_from_tarball(
                f"report_id_{report_id}/details.json", tarball
            )
            assert tarball_details_dict == details_response.json()

            tarball_deployments_dict = load_json_from_tarball(
                f"report_id_{report_id}/deployments.json", tarball
            )
            assert tarball_deployments_dict == deployments_response.json()
