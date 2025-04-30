"""Abstraction for retrieving data from OpenShift/Kubernetes API."""

from __future__ import annotations

import contextlib
import json
from functools import cached_property, wraps
from logging import getLogger
from typing import List

from kubernetes.client import ApiClient, ApiException, CoreV1Api
from kubernetes.client import Configuration as KubeConfig
from kubernetes.dynamic.exceptions import ResourceNotFoundError
from openshift.dynamic import DynamicClient
from openshift.helper.userpassauth import OCPLoginConfiguration
from urllib3.exceptions import MaxRetryError

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

logger = getLogger(__name__)


def catch_k8s_exception(func):
    """Capture Kubernetes exception and reraise as OCPError."""

    @wraps(func)
    def _decorator(*args, **kwargs):
        _normalize_kwargs(kwargs)
        try:
            return func(*args, **kwargs)
        except ApiException as api_exception:
            ocp_error = OCPError.from_api_exception(api_exception)
            raise ocp_error from api_exception
        except MaxRetryError as error:
            raise OCPError(
                status=-1,
                reason=error.reason.__class__.__name__,
                message=str(error.reason),
            ) from error

    def _normalize_kwargs(kwargs):
        """Normalize kwargs before sending them to internal k8s api calls."""
        timeout = kwargs.pop("timeout_seconds", None)
        if timeout:
            # translate "timeout_seconds" to its internal equivalent
            # https://github.com/kubernetes-client/python/blob/9df5fa766631beb071a2cff36c839e8b8ffa911b/kubernetes/client/api_client.py#L125
            kwargs["_request_timeout"] = timeout

    return _decorator


def optional_openshift_resource(resource_name: str, empty_return_type: type = list):
    """
    Handle ResourceNotFoundError if the host does not support the given resource.

    Returns an empty list if the resource is not found.
    """

    def _optional_openshift_resource(func):
        @wraps(func)
        def _wrapped_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ResourceNotFoundError:
                logger.info(
                    "This OpenShift host does not have %(resource_name)s.",
                    {"resource_name": resource_name},
                )
                return empty_return_type()

        return _wrapped_func

    return _optional_openshift_resource


class OpenShiftApi:
    """OpenShift interface for Quipucords."""

    def __init__(
        self,
        configuration: KubeConfig,
    ):
        """Initialize OpenShiftApi."""
        self._configuration = configuration
        self._api_client = ApiClient(configuration=self._configuration)
        # discoverer cache is used to cache resources for dynamic client
        self._discoverer_cache_file = None

    @cached_property
    def _dynamic_client(self):
        # decorate DynamicClient to catch k8s exceptions
        dynamic_client = catch_k8s_exception(DynamicClient)
        return dynamic_client(
            self._api_client,
            cache_file=self._discoverer_cache_file,
        )

    @classmethod
    def with_config_info(
        cls,
        *,
        host,
        protocol,
        port,
        ssl_verify: bool = True,
        proxy_url: str = None,
        **kwargs,
    ):
        """Initialize OpenShiftApi without providing a KubeConfig object."""
        host_uri = f"{protocol}://{host}:{port}"

        if kwargs.get("auth_token"):
            kube_config = cls._init_kube_config(
                host_uri, ssl_verify=ssl_verify, **kwargs
            )
        else:
            kube_config = cls._init_ocp_login_config(
                host_uri, ssl_verify=ssl_verify, **kwargs
            )
        if proxy_url:
            kube_config.proxy = {protocol: proxy_url}
        return cls(configuration=kube_config)

    @classmethod
    def _init_kube_config(cls, host, *, ssl_verify, auth_token):
        kube_config = KubeConfig(
            host=host,
            api_key={"authorization": f"bearer {auth_token}"},
        )
        kube_config.verify_ssl = ssl_verify
        return kube_config

    @classmethod
    def _init_ocp_login_config(
        cls,
        host,
        username,
        password,
        ssl_verify,
    ):
        """Start a specialized KubeConfig that uses OCP username+password."""
        config = OCPLoginConfiguration(
            host=host,
            ocp_username=username,
            ocp_password=password,
        )
        config.verify_ssl = ssl_verify
        config.get_token()
        return config

    def can_connect(self, raise_exception=False, **kwargs):
        """Check if it's possible to connect to OCP host."""
        try:
            # call a lightweight endpoint just to check if we can
            # stablish a connection
            catch_k8s_exception(self._core_api.get_api_resources)(**kwargs)
        except OCPError as err:
            if raise_exception:
                raise err
            logger.error("Unable to connect to OCP/K8S api (status=%s)", err.status)
            return False
        except Exception:
            if raise_exception:
                raise
            logger.exception("Got an unexpected exception. Check system logs.")
            return False
        return True

    # Adding support for fetching OCP Prometheus Metrics
    # Reference: https://access.redhat.com/solutions/3775611

    @catch_k8s_exception
    def metrics_query(self, query):
        """Execute an OpenShift Prometheus Query."""
        kube_config = self._configuration
        metrics_host = self._metrics_host()
        if not metrics_host:
            return []
        response = self._api_client.request(
            "GET",
            url=f"https://{metrics_host}/api/v1/query",
            query_params={"query": query},
            headers=kube_config.api_key,
        )

        json_response = json.loads(response.data)
        return [r["metric"] for r in json_response["data"]["result"]]

    @catch_k8s_exception
    def _metrics_host(self):
        """Return the Prometheus host to use for accessing metrics."""
        route_list = self._list_routes(
            namespace="openshift-monitoring",
            field_selector="metadata.name=prometheus-k8s",
        )
        if len(route_list) != 1:
            logger.warning(
                "Could not find the OpenShift prometheus-k8s metrics route,"
                " querying metrics will be disabled."
            )
            return None
        return route_list[0]["spec"]["host"]

    def retrieve_nodes(self, **kwargs) -> List[OCPNode]:
        """Retrieve nodes under OCP host."""
        node_list = []
        for node in self._list_nodes(**kwargs):
            ocp_node = self._init_ocp_nodes(node)
            node_list.append(ocp_node)
        return node_list

    def retrieve_cluster(self, **kwargs) -> OCPCluster:
        """Retrieve cluster under OCP host."""
        clusters = self._list_clusters(**kwargs)
        if len(clusters) > 1:
            raise ValueError("More than one cluster in cluster API")
        cluster_entity = self._init_cluster(clusters[0])
        return cluster_entity

    def retrieve_rhacm_metrics(self, **kwargs) -> list:
        """Retrieve metrics on RHACM managed clusters."""
        rhacm_metrics = []
        for cluster in self._list_managed_clusters(**kwargs):
            managed_cluster_metrics = self._init_managed_cluster(cluster)
            rhacm_metrics.append(managed_cluster_metrics)
        return rhacm_metrics

    def retrieve_pods(self, **kwargs) -> List[OCPPod]:
        """Retrieve OCP Pods."""
        pods_raw = self._list_pods(**kwargs)
        pods_list = []
        for pod in pods_raw:
            ocp_pod = OCPPod.from_api_object(pod)
            pods_list.append(ocp_pod)
        return pods_list

    def retrieve_workloads(self, **kwargs) -> List[OCPWorkload]:
        """Retrieve OCPWorkloads."""
        pod_list = self.retrieve_pods(**kwargs)
        _app_names = set()
        workload_list = []
        for pod in pod_list:
            pod_id = (pod.namespace, pod.app_name)
            if pod_id in _app_names:
                continue
            _app_names.add(pod_id)
            data = pod.dict()
            data["name"] = pod.app_name
            workload_list.append(OCPWorkload(**data))
        return workload_list

    def retrieve_operators(self, **kwargs) -> List[ClusterOperator | LifecycleOperator]:
        """Retrieve cluster and "olm" operators."""
        cluster_operators = [
            ClusterOperator.from_raw_object(operator)
            for operator in self._list_cluster_operators(**kwargs)
        ]
        olm_operators = [
            LifecycleOperator.from_raw_object(operator)
            for operator in self._list_subscriptions(**kwargs)
        ]
        # Use CSV api to enhance olm operators with extra metadata
        csv_map = {
            csv.metadata.name: csv
            for csv in self._list_cluster_service_versions(**kwargs)
        }
        for operator in olm_operators:
            # We suppress KeyError below because sometimes we find an operator that
            # wasn't listed in the cluster service versions. I'm not sure how this can
            # happen, but we have actually seen it on a shared OpenShift server.
            # See related: https://github.com/quipucords/quipucords/pull/2447
            # In that case, `operator.display_name` keeps its default `None` which
            # we prefer over choosing some other value.
            with contextlib.suppress(KeyError):
                csv = csv_map[operator.cluster_service_version]
                operator.display_name = csv.spec.displayName

        return cluster_operators + olm_operators

    @cached_property
    def _core_api(self):
        return CoreV1Api(api_client=self._api_client)

    @cached_property
    def _node_api(self):
        return self._dynamic_client.resources.get(api_version="v1", kind="Node")

    @cached_property
    def _namespace_api(self):
        return self._dynamic_client.resources.get(api_version="v1", kind="Namespace")

    @cached_property
    def _cluster_api(self):
        return self._dynamic_client.resources.get(
            api_version="config.openshift.io/v1", kind="ClusterVersion"
        )

    @cached_property
    def _pod_api(self):
        return self._dynamic_client.resources.get(api_version="v1", kind="Pod")

    @cached_property
    def _cluster_operator_api(self):
        return self._dynamic_client.resources.get(
            api_version="config.openshift.io/v1", kind="ClusterOperator"
        )

    @cached_property
    def _route_api(self):
        return self._dynamic_client.resources.get(
            api_version="route.openshift.io/v1", kind="Route"
        )

    @cached_property
    def _subscription_api(self):
        return self._dynamic_client.resources.get(
            api_version="operators.coreos.com/v1alpha1", kind="Subscription"
        )

    @cached_property
    def _cluster_service_version_api(self):
        return self._dynamic_client.resources.get(
            api_version="operators.coreos.com/v1alpha1", kind="ClusterServiceVersion"
        )

    @cached_property
    def _managed_cluster_api(self):
        return self._dynamic_client.resources.get(
            api_version="cluster.open-cluster-management.io/v1", kind="ManagedCluster"
        )

    @catch_k8s_exception
    def _list_nodes(self, **kwargs):
        return self._node_api.get(**kwargs).items

    @catch_k8s_exception
    def _list_clusters(self, **kwargs):
        return self._cluster_api.get(**kwargs).items

    @catch_k8s_exception
    def _list_pods(self, **kwargs):
        return self._pod_api.get(**kwargs).items

    @catch_k8s_exception
    def _list_cluster_operators(self, **kwargs):
        return self._cluster_operator_api.get(**kwargs).items

    @catch_k8s_exception
    def _list_subscriptions(self, **kwargs):
        return self._subscription_api.get(**kwargs).items

    @catch_k8s_exception
    def _list_cluster_service_versions(self, **kwargs):
        return self._cluster_service_version_api.get(**kwargs).items

    @catch_k8s_exception
    @optional_openshift_resource("ManagedCluster API")
    def _list_managed_clusters(self, **kwargs):
        return self._managed_cluster_api.get(**kwargs).items

    @catch_k8s_exception
    def _list_routes(self, **kwargs):
        return self._route_api.get(**kwargs).items

    def _init_ocp_nodes(self, node) -> OCPNode:
        # following upstream docs[1], if unschedulable is None, it is considered
        # false.
        # [1]: https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/node-v1/#NodeSpec
        unschedulable = node.spec["unschedulable"] or False
        return OCPNode(
            name=node.metadata.name,
            creation_timestamp=node.metadata.creationTimestamp,
            labels=node.metadata.labels,
            addresses=node.status["addresses"],
            allocatable=NodeResources(
                cpu=node.status["allocatable"]["cpu"],
                memory_in_bytes=node.status["allocatable"]["memory"],
                pods=node.status["allocatable"]["pods"],
            ),
            capacity=NodeResources(
                cpu=node.status["capacity"]["cpu"],
                memory_in_bytes=node.status["capacity"]["memory"],
                pods=node.status["capacity"]["pods"],
            ),
            architecture=node.status["nodeInfo"]["architecture"],
            kernel_version=node.status["nodeInfo"]["kernelVersion"],
            machine_id=node.status["nodeInfo"]["machineID"],
            operating_system=node.status["nodeInfo"]["operatingSystem"],
            taints=node.spec["taints"],
            unschedulable=unschedulable,
        )

    def _init_cluster(self, cluster) -> OCPCluster:
        ocp_cluster = OCPCluster(
            uuid=cluster["spec"]["clusterID"],
            version=cluster["status"]["desired"]["version"],
        )
        return ocp_cluster

    def _init_managed_cluster(self, cluster) -> dict:
        managed_cluster_metrics = {}

        key_map_labels = {
            "vendor": "vendor",
            "cloud": "cloud",
            "version": "openshiftVersion",
            "managed_cluster_id": "clusterID",
        }

        labels = cluster["metadata"]["labels"]
        for metric_key, cluster_api_key in key_map_labels.items():
            managed_cluster_metrics[metric_key] = labels[cluster_api_key]

        conditions = cluster["status"]["conditions"]
        is_cluster_available = any(
            condition.get("reason") == "ManagedClusterAvailable"
            for condition in conditions
        )
        managed_cluster_metrics["available"] = is_cluster_available

        capacity = cluster["status"].get("capacity", {})
        managed_cluster_metrics["core_worker"] = capacity.get("core_worker")
        managed_cluster_metrics["socket_worker"] = capacity.get("socket_worker")
        managed_cluster_metrics["created_via"] = cluster["metadata"]["annotations"][
            "open-cluster-management/created-via"
        ]
        return managed_cluster_metrics
