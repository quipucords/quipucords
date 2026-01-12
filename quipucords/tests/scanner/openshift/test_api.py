"""Abstraction for retrieving data from OpenShift/Kubernetes API."""

import logging
import random
from pathlib import Path
from unittest import mock
from uuid import UUID

import httpretty
import pytest
import requests
from kubernetes.client import Configuration as KubeConfig
from kubernetes.dynamic.exceptions import ResourceNotFoundError
from kubernetes.dynamic.resource import ResourceInstance
from requests.exceptions import InvalidURL

from scanner.openshift.api import OpenShiftApi, optional_openshift_resource
from scanner.openshift.entities import (
    ClusterOperator,
    LifecycleOperator,
    NodeResources,
    OCPCluster,
    OCPError,
    OCPNode,
    OCPPod,
    OCPWorkload,
)
from tests.asserts import assert_elements_type
from tests.constants import ConstantsFromEnv, VCRCassettes


def data_path(filename) -> Path:
    """Path object for testing data."""
    return Path(__file__).parent / "test_data" / filename


class TestData:
    """
    Constants holding path for OCP Rest Api responses.

    They are based on real data and then were tweaked/reduced for testing purposes.
    """

    API_RESOURCE_LIST = data_path("api_resource_list.json")
    UNAUTHORIZED_RESPONSE = data_path("unauthorized_response.json")


def patch_ocp_api(path, **kwargs):
    """Shortcut for patching ocp requests."""
    ocp_uri = ConstantsFromEnv.TEST_OCP_URI.value
    httpretty.register_uri(
        httpretty.GET,
        f"{ocp_uri.protocol}://{ocp_uri.host}:{ocp_uri.port}/{path}",
        **kwargs,
    )


def dynamic_scope(fixture_name, config):
    """Set scope to session when running with --refresh-cassettes."""
    if config.getoption("--refresh-cassettes", None):
        return "session"
    return "function"


@pytest.fixture(scope=dynamic_scope)
def discoverer_cache(request):
    """OCP dynamic client "discoverer" cache."""
    fname = "ocp-discovery.json"
    if request.config.getoption("--refresh-cassettes"):
        # persist cache file for whole test suite execution
        tmp_path_factory = request.getfixturevalue("tmp_path_factory")
        _file = tmp_path_factory.mktemp("ocp-cache") / fname
        _file.parent.mkdir(parents=True, exist_ok=True)
        yield _file

    else:
        yield request.getfixturevalue("tmp_path") / fname


@pytest.fixture(scope=dynamic_scope)
def ocp_client(request, discoverer_cache):
    """OCP client for testing."""
    ocp_uri = ConstantsFromEnv.TEST_OCP_URI.value
    auth_token = getattr(request, "param", ConstantsFromEnv.TEST_OCP_AUTH_TOKEN.value)
    client = OpenShiftApi.with_config_info(
        auth_token=auth_token,
        host=ocp_uri.host,
        port=ocp_uri.port,
        protocol=ocp_uri.protocol,
        ssl_verify=ConstantsFromEnv.TEST_OCP_SSL_VERIFY.value,
    )
    client._discoverer_cache_file = discoverer_cache
    yield client


@pytest.mark.vcr_primer(VCRCassettes.OCP_UNAUTHORIZED)
@pytest.mark.vcr(match_on=["method", "scheme", "host", "port", "query"])
@pytest.mark.parametrize("ocp_client", ["<INVALID_AUTH_TOKEN>"], indirect=True)
@pytest.mark.parametrize("api_method", ["_dynamic_client"])
def test_unauthorized_token(ocp_client: OpenShiftApi, api_method):
    """Test calling OCP with an invalid token."""
    with pytest.raises(OCPError) as exc_info:
        client_attr = getattr(ocp_client, api_method)
        # if error wasn't thrown in previous line, let's assume attribute is a callable
        client_attr()
    assert exc_info.value.status == 401
    assert exc_info.value.reason == "Unauthorized"


@pytest.mark.vcr_primer(VCRCassettes.OCP_DISCOVERER_CACHE)
def test_dynamic_client_cache(ocp_client: OpenShiftApi):
    """
    Test dynamic_client cache.

    Whenever a new "api resource" is added to ocp_client we need to add it to this test
    and run `pytest --refresh-cassettes` using a valid OCP connection.
    """
    assert not ocp_client._discoverer_cache_file.exists(), (
        "Cache file exists prior to test execution!"
    )
    # just accessing the attribute will trigger "introspection" requests at ocp
    ocp_client._dynamic_client
    ocp_client._cluster_api
    ocp_client._node_api
    ocp_client._namespace_api
    ocp_client._pod_api
    ocp_client._cluster_operator_api
    ocp_client._route_api
    ocp_client._subscription_api
    ocp_client._cluster_service_version_api
    ocp_client._managed_cluster_api
    assert Path(ocp_client._discoverer_cache_file).exists()


@pytest.mark.vcr_primer(VCRCassettes.OCP_CLUSTER, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_cluster_api(ocp_client: OpenShiftApi):
    """Test _cluster_api."""
    clusters = ocp_client._list_clusters()
    assert clusters


@pytest.mark.vcr_primer(
    VCRCassettes.OCP_CLUSTER_OPERATORS, VCRCassettes.OCP_DISCOVERER_CACHE
)
def test_cluster_operators_api(ocp_client: OpenShiftApi):
    """Test _cluster_api."""
    cluster_operators = ocp_client._list_cluster_operators()
    assert cluster_operators


@pytest.mark.vcr_primer(VCRCassettes.OCP_ROUTE, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_route_api(ocp_client: OpenShiftApi):
    """Test _route_api."""
    routes = ocp_client._list_routes()
    assert routes


@pytest.mark.vcr(VCRCassettes.OCP_ROUTE, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_list_route(ocp_client: OpenShiftApi):
    """Test retrieve routes method."""
    list_routes = ocp_client._list_routes()
    for route in list_routes:
        assert route["spec"]["host"]


@pytest.mark.vcr_primer(
    VCRCassettes.OCP_SUBSCRIPTIONS, VCRCassettes.OCP_DISCOVERER_CACHE
)
def test_subscriptions_api(ocp_client: OpenShiftApi):
    """Test _cluster_api."""
    subscriptions = ocp_client._list_subscriptions()
    assert subscriptions


@pytest.mark.vcr_primer(VCRCassettes.OCP_CSV, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_csv_api(ocp_client: OpenShiftApi):
    """Test _list_cluster_service_versions."""
    csv_list = ocp_client._list_cluster_service_versions()
    assert csv_list


@pytest.mark.vcr_primer(VCRCassettes.OCP_ACM, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_cluster_rhacm_api(ocp_client: OpenShiftApi):
    """Test _managed_cluster_api."""
    rhacm_metrics = ocp_client._list_managed_clusters()
    assert rhacm_metrics


@pytest.mark.vcr(VCRCassettes.OCP_CLUSTER, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_retrieve_cluster(ocp_client: OpenShiftApi):
    """Test retrieve cluster method."""
    cluster = ocp_client.retrieve_cluster()
    assert isinstance(cluster, OCPCluster)
    assert UUID(cluster.uuid)
    assert cluster.version


@pytest.mark.vcr(
    VCRCassettes.OCP_CLUSTER_OPERATORS,
    VCRCassettes.OCP_SUBSCRIPTIONS,
    VCRCassettes.OCP_CSV,
    VCRCassettes.OCP_DISCOVERER_CACHE,
)
def test_retrieve_operators(ocp_client: OpenShiftApi):
    """Test retrieve operators method."""
    operators = ocp_client.retrieve_operators()
    assert isinstance(operators, list)
    assert isinstance(operators[0], ClusterOperator)
    # OCP instance used on VCR preparation should have at least one lifecycle operator
    # installed (doesn't matter which one)
    assert isinstance(operators[-1], LifecycleOperator)


@pytest.mark.vcr(
    VCRCassettes.OCP_ACM,
    VCRCassettes.OCP_DISCOVERER_CACHE,
)
def test_retrieve_rhacm_metrics(ocp_client: OpenShiftApi):
    """Test retrieve RHACM metrics method."""
    # OCP instance used on VCR preparation should have RHACM operator installed,
    # with active multiClusterHub instance
    rhacm_metrics = ocp_client.retrieve_rhacm_metrics()
    assert isinstance(rhacm_metrics, list)
    min_cluster_msg = "This test requires at least 1 cluster managed through RHACM."
    assert len(rhacm_metrics) >= 1, min_cluster_msg

    # The following assertion is based on the assumption that the provisioned cluster
    # has not undergone any additional config modifications. When creating the
    # multiClusterHub instance, it is expected that at least one managed cluster will
    # be discovered, the hub itself. An associated set of keys is expected.
    # The "available" key within these metrics is expected to be True, indicating that
    # the cluster is available and configured properly.

    expected_keys = [
        "vendor",
        "cloud",
        "version",
        "managed_cluster_id",
        "available",
        "core_worker",
        "socket_worker",
        "created_via",
    ]
    expected_data = [{key: mock.ANY for key in expected_keys}] * len(rhacm_metrics)
    assert rhacm_metrics == expected_data
    # at least one cluster is available
    assert any(cluster_metrics["available"] for cluster_metrics in rhacm_metrics)


@pytest.mark.parametrize(
    "status_info, expected_metrics",
    [
        (
            {
                "conditions": [{"reason": "ManagedClusterAvailable"}],
                "capacity": {"core_worker": 4, "socket_worker": 2},
            },
            [
                {
                    "available": True,
                    "cloud": "cloud1",
                    "core_worker": 4,
                    "created_via": "via1",
                    "managed_cluster_id": "id1",
                    "socket_worker": 2,
                    "vendor": "vendor1",
                    "version": "version1",
                }
            ],
        ),
        (
            {
                "conditions": [
                    {"reason": "ManagedClusterWaitForImporting"},
                    {"reason": "HubClusterAdminAccepted"},
                ],
            },
            [
                {
                    "available": False,
                    "cloud": "cloud1",
                    "core_worker": None,
                    "created_via": "via1",
                    "managed_cluster_id": "id1",
                    "socket_worker": None,
                    "vendor": "vendor1",
                    "version": "version1",
                }
            ],
        ),
        (
            {
                "conditions": [
                    {"reason": "ManagedClusterWaitForImporting"},
                    {"reason": "ManagedClusterAvailable"},
                ],
                "capacity": {"cpu": 24},
            },
            [
                {
                    "available": True,
                    "cloud": "cloud1",
                    "core_worker": None,
                    "created_via": "via1",
                    "managed_cluster_id": "id1",
                    "socket_worker": None,
                    "vendor": "vendor1",
                    "version": "version1",
                }
            ],
        ),
    ],
)
def test_init_managed_cluster(
    ocp_client: OpenShiftApi, mocker, status_info, expected_metrics
):
    """Test logic creating managed cluster metrics dict."""
    mock_managed_cluster = {
        "metadata": {
            "labels": {
                "vendor": "vendor1",
                "cloud": "cloud1",
                "openshiftVersion": "version1",
                "clusterID": "id1",
            },
            "annotations": {"open-cluster-management/created-via": "via1"},
        },
        "status": status_info,
    }

    mocker.patch.object(
        ocp_client,
        "_list_managed_clusters",
        return_value=[mock_managed_cluster],
    )

    rhacm_metrics = ocp_client.retrieve_rhacm_metrics()

    assert rhacm_metrics == expected_metrics


def test_optional_openshift_resource(caplog):
    """Test optional_openshift_resource handles the normal happy path case."""
    expected_things = [1, 2, "a", "b"]

    @optional_openshift_resource("optional thing API")
    def _list_optional_things():
        return expected_things

    caplog.set_level(logging.INFO)
    assert _list_optional_things() == expected_things
    assert len(caplog.messages) == 0


def test_optional_openshift_resource_missing(caplog):
    """Test optional_openshift_resource gracefully handles a missing OpenShift API."""

    @optional_openshift_resource("optional thing API")
    def _list_optional_things():
        # Normally a call like this would be invoked on an OpenShiftApi client.
        # For the sake of testing, we simply want to force a client exception.
        # This emulates the client's behavior when the caller requests a resource that
        # the server does not have, as may happen for optional features like RHACM.
        raise ResourceNotFoundError

    caplog.set_level(logging.INFO)
    assert _list_optional_things() == []
    assert caplog.messages == ["This OpenShift host does not have optional thing API."]


@pytest.mark.parametrize(
    "empty_return_type, expected_output", ((list, []), (dict, {}), (type(None), None))
)
def test_optional_openshift_resource_missing_custom_empty_return_type(
    empty_return_type, expected_output
):
    """Test optional_openshift_resource returns an instance of the specified type."""

    @optional_openshift_resource("optional thing API", empty_return_type)
    def _list_optional_things():
        raise ResourceNotFoundError

    if expected_output is None:
        assert _list_optional_things() is None
    else:
        assert _list_optional_things() == expected_output


def test_olm_operator_construction(ocp_client: OpenShiftApi, mocker, faker):
    """Test logic creating LifecycleOperator."""
    operator_csv = "papaya_operator.v1.2.3"
    operator_display_name = "Papaya Operator"

    subscription = mocker.Mock()
    subscription.status.currentCSV = operator_csv
    subscription.metadata.name = faker.slug()
    subscription.metadata.creationTimestamp = faker.date_time()
    subscription.status.lastUpdated = faker.date_time()
    subscription.metadata.namespace = faker.slug()
    subscription.spec.channel = faker.slug()
    subscription.spec.source = faker.slug()

    csv = mocker.Mock()
    csv.metadata.name = operator_csv
    csv.spec.displayName = operator_display_name

    mocker.patch.object(OpenShiftApi, "_list_cluster_operators")
    mocker.patch.object(
        OpenShiftApi,
        "_list_subscriptions",
        return_value=[subscription],
    )
    mocker.patch.object(
        OpenShiftApi,
        "_list_cluster_service_versions",
        return_value=[csv],
    )

    operators = ocp_client.retrieve_operators()
    assert len(operators) == 1
    assert operators[0].display_name == operator_display_name
    assert operators[0].cluster_service_version == operator_csv


@pytest.mark.vcr_primer(VCRCassettes.OCP_NODE, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_node_api(ocp_client: OpenShiftApi):
    """Test _node_api."""
    nodes = ocp_client._list_nodes()
    assert nodes


@pytest.mark.vcr(VCRCassettes.OCP_NODE, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_retrieve_node(ocp_client: OpenShiftApi):
    """Test retrieve node method."""
    list_nodes = ocp_client.retrieve_nodes()
    for node in list_nodes:
        assert isinstance(node, OCPNode)
        assert isinstance(node.allocatable, NodeResources)
        assert isinstance(node.capacity, NodeResources)
        assert node.name


def test_with_config_info_using_auth_token(mocker):
    """Test factory method with_config_info with auth_token."""
    patched_kube_config = mocker.patch("scanner.openshift.api.KubeConfig")
    patched_api_client = mocker.patch("scanner.openshift.api.ApiClient")
    client = OpenShiftApi.with_config_info(
        host="HOST", protocol="PROT", port="PORT", auth_token="TOKEN"
    )
    assert isinstance(client, OpenShiftApi)
    assert patched_kube_config.mock_calls == [
        mocker.call(
            host="PROT://HOST:PORT",
            api_key={"authorization": "bearer TOKEN"},
        )
    ]
    assert patched_api_client.mock_calls == [
        mocker.call(configuration=patched_kube_config()),
    ]
    assert client._api_client == patched_api_client()


@httpretty.activate
def test_can_connect(ocp_client: OpenShiftApi):
    """Test if connection to OCP host is succesful when it should be."""
    patch_ocp_api(
        "api/v1/",
        body=TestData.API_RESOURCE_LIST.read_text(),
    )
    assert ocp_client.can_connect()


@httpretty.activate
def test_cannot_connect(
    ocp_client: OpenShiftApi,
    caplog,
):
    """Test if connection to OCP host is not sucessful when it should not be."""
    patch_ocp_api(
        "api/v1/",
        body=TestData.UNAUTHORIZED_RESPONSE.read_text(),
        status=401,
    )
    assert not ocp_client.can_connect()
    assert caplog.messages[-1] == "Unable to connect to OCP/K8S api (status=401)"


@pytest.mark.vcr_primer(VCRCassettes.OCP_PODS, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_pods_api(ocp_client: OpenShiftApi):
    """Test pods api."""
    pods = ocp_client._list_pods()
    assert pods


@pytest.mark.vcr(VCRCassettes.OCP_PODS, VCRCassettes.OCP_DISCOVERER_CACHE)
def test_retrieve_pods(ocp_client: OpenShiftApi):
    """Test retrieving pods."""
    pods = ocp_client.retrieve_pods()
    assert_elements_type(pods, OCPPod)


@pytest.mark.vcr(
    VCRCassettes.OCP_PODS,
    VCRCassettes.OCP_DISCOVERER_CACHE,
    allow_playback_repeats=True,
)
def test_retrieve_workloads(ocp_client: OpenShiftApi):
    """Test retrieving workloads."""
    pods = ocp_client.retrieve_pods()
    workloads = ocp_client.retrieve_workloads()
    assert_elements_type(workloads, OCPWorkload)
    assert len(workloads) < len(pods)
    assert {p.app_name for p in pods} == {a.name for a in workloads}


@pytest.fixture
def node_metrics_query():
    """Return a simple node metrics query."""
    return "count by(instance) (max by(node, instance) (cluster:cpu_core_node_labels))"


@pytest.mark.vcr_primer(
    VCRCassettes.OCP_METRICS_CACHE,
    VCRCassettes.OCP_DISCOVERER_CACHE,
)
def test_metrics_query(
    ocp_client: OpenShiftApi,
    node_metrics_query,
    mocker,
):
    """Test Prometheus query is properly parsed and returned."""
    mocker.patch.object(
        ocp_client,
        "_metrics_host",
        return_value=ConstantsFromEnv.TEST_OCP_METRICS_URI.value.host,
    )
    query_response = ocp_client.metrics_query(node_metrics_query)

    # Make sure metrics_query has properly extracted the metric out of the
    # Prometheus response (and not in the response returned) and that the
    # query did return the instance being asked for.
    for query_item in query_response:
        assert "instance" in query_item
        assert "metric" not in query_item


@pytest.mark.vcr(VCRCassettes.OCP_DISCOVERER_CACHE, VCRCassettes.OCP_NODE)
@pytest.mark.parametrize(
    "expected_value,unschedulable",
    (
        (False, None),
        (False, False),
        (True, True),
    ),
)
def test_unschedulable_logic(
    ocp_client: OpenShiftApi, mocker, expected_value, unschedulable
):
    """Test if OCPNode.unschedulable is correctly inferred from OCP API."""
    # monkeypatch a real representation of Node in order to test this logic.
    # This can't be done (or at least I couldn't figure out a way) to mock
    # it directly - ResourceInstance and ResourceField objects are not friendly
    # to mock, nor accepts direct assignment.
    raw_node = random.choice(ocp_client._list_nodes())
    raw_node_dict = raw_node.to_dict()
    raw_node_dict["spec"]["unschedulable"] = unschedulable
    mocked_node = ResourceInstance(mocker.Mock(), raw_node_dict)

    node = ocp_client._init_ocp_nodes(mocked_node)
    assert isinstance(node, OCPNode)
    assert node.unschedulable == expected_value


def test_with_config_info_passes_proxy_to_apiclient(mocker):
    """
    Ensure a valid proxy_url is applied to KubeConfig and ApiClient is called.

    This test may seem trivial, but it's important. We previously passed the proxy
    as a dict, which caused a TypeError deep in urllib3 when ApiClient was
    initialized. This test reproduces the condition where that bug would have been
    exposed (i.e., during client initialization), and ensures no exception is raised
    when using a string, as expected.

    If the initialization logic regresses, this test will fail — even without making
    real requests.
    """
    kube_config_mock = mocker.Mock()
    mocker.patch("scanner.openshift.api.KubeConfig", return_value=kube_config_mock)
    patched_api_client = mocker.patch("scanner.openshift.api.ApiClient")

    proxy_url = "http://proxy.example.com:8080"
    client = OpenShiftApi.with_config_info(
        host="HOST",
        protocol="https",
        port="443",
        auth_token="TOKEN",
        proxy_url=proxy_url,
    )

    assert hasattr(kube_config_mock, "proxy")
    assert proxy_url in str(kube_config_mock.proxy)

    patched_api_client.assert_called_once_with(configuration=kube_config_mock)
    assert isinstance(client, OpenShiftApi)


def test_with_config_info_does_not_set_proxy_when_none(mocker):
    """Ensure proxy is not set on KubeConfig when proxy_url is None."""
    kube_config_mock = mocker.Mock(spec=KubeConfig)
    _ = mocker.patch(  # noqa: F841
        "scanner.openshift.api.KubeConfig", return_value=kube_config_mock
    )
    patched_api_client = mocker.patch("scanner.openshift.api.ApiClient")

    client = OpenShiftApi.with_config_info(
        host="HOST", protocol="https", port="443", auth_token="TOKEN", proxy_url=None
    )

    assert not hasattr(kube_config_mock, "proxy")
    assert isinstance(client, OpenShiftApi)
    patched_api_client.assert_called_once_with(configuration=kube_config_mock)


def test_initialize_openshiftapi_with_proxy_config():
    """
    Ensure OpenShiftApi initializes successfully with a proxy URL.

    This integration-style test verifies that initializing OpenShiftApi with a
    proxy does not raise a TypeError. Previously, a dictionary was incorrectly
    passed to proxy_url, causing urllib3.ProxyManager to fail.

    The test avoids mocks to reproduce the actual failure scenario and prevent
    regressions. No assertions are needed; if initialization fails, the test
    will naturally error out.
    """
    OpenShiftApi.with_config_info(
        host="HOST",
        protocol="https",
        port="443",
        auth_token="TOKEN",
        proxy_url="http://proxy.example.com:8080/",
    )


def test_with_config_info_with_ipv6_host(mocker):
    """Test that IPv6 hosts are properly formatted in the URL."""
    patched_kube_config = mocker.patch("scanner.openshift.api.KubeConfig")
    mocker.patch("scanner.openshift.api.ApiClient")

    OpenShiftApi.with_config_info(
        host="fd00:dead:beef::126",
        protocol="https",
        port="6443",
        auth_token="TOKEN",
    )

    patched_kube_config.assert_called_once_with(
        host="https://[fd00:dead:beef::126]:6443",
        api_key={"authorization": "bearer TOKEN"},
    )


def test_ipv6_url_without_brackets_fails():
    """Document that requests fails to parse IPv6 URLs without brackets.

    This test demonstrates the issue that _format_host_for_url solves.
    """
    with pytest.raises(InvalidURL, match="Failed to parse"):
        requests.get("http://fd00:dead:beef::126:6443/", timeout=0.1)
