"""Abstraction for retrieving data from OpenShift/Kubernetes API."""

from __future__ import annotations

import contextlib
from functools import cached_property, wraps
from logging import getLogger
from typing import List

from kubernetes.client import ApiClient, ApiException, CoreV1Api
from kubernetes.client import Configuration as KubeConfig
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
        cls, *, host, protocol, port, ssl_verify: bool = True, **kwargs
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

    def retrieve_nodes(self, **kwargs) -> List[OCPNode]:
        """Retrieve nodes under OCP host."""
        node_list = []
        for node in self._list_nodes(**kwargs).items:
            ocp_node = self._init_ocp_nodes(node)
            node_list.append(ocp_node)
        return node_list

    def retrieve_cluster(self, **kwargs) -> OCPCluster:
        """Retrieve cluster under OCP host."""
        clusters = self._list_clusters(**kwargs).items
        assert len(clusters) == 1, "More than one cluster in cluster API"
        cluster_entity = self._init_cluster(clusters[0])
        return cluster_entity

    def retrieve_pods(self, **kwargs) -> List[OCPPod]:
        """Retrieve OCP Pods."""
        pods_raw = self._list_pods(**kwargs)
        pods_list = []
        for pod in pods_raw.items:
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
            for operator in self._list_cluster_operators(**kwargs).items
        ]
        olm_operators = [
            LifecycleOperator.from_raw_object(operator)
            for operator in self._list_subscriptions(**kwargs).items
        ]
        # Use CSV api to enhance olm operators with extra metadata
        csv_map = {
            csv.metadata.name: csv
            for csv in self._list_cluster_service_versions(**kwargs).items
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
    def _subscription_api(self):
        return self._dynamic_client.resources.get(
            api_version="operators.coreos.com/v1alpha1", kind="Subscription"
        )

    @cached_property
    def _cluster_service_version_api(self):
        return self._dynamic_client.resources.get(
            api_version="operators.coreos.com/v1alpha1", kind="ClusterServiceVersion"
        )

    @catch_k8s_exception
    def _list_nodes(self, **kwargs):
        return self._node_api.get(**kwargs)

    @catch_k8s_exception
    def _list_clusters(self, **kwargs):
        return self._cluster_api.get(**kwargs)

    @catch_k8s_exception
    def _list_pods(self, **kwargs):
        return self._pod_api.get(**kwargs)

    @catch_k8s_exception
    def _list_cluster_operators(self, **kwargs):
        return self._cluster_operator_api.get(**kwargs)

    @catch_k8s_exception
    def _list_subscriptions(self, **kwargs):
        return self._subscription_api.get(**kwargs)

    @catch_k8s_exception
    def _list_cluster_service_versions(self, **kwargs):
        return self._cluster_service_version_api.get(**kwargs)

    def _init_ocp_nodes(self, node) -> OCPNode:
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
        )

    def _init_cluster(self, cluster) -> OCPCluster:
        ocp_cluster = OCPCluster(
            uuid=cluster["spec"]["clusterID"],
            version=cluster["status"]["desired"]["version"],
        )
        return ocp_cluster
