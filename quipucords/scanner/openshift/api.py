# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Abstraction for retrieving data from OpenShift/Kubernetes API."""

from functools import cached_property, wraps
from logging import getLogger
from typing import List

from kubernetes.client import (
    ApiClient,
    ApiException,
    AppsV1Api,
    Configuration,
    CoreV1Api,
)
from openshift.dynamic import DynamicClient
from urllib3.exceptions import MaxRetryError

from scanner.openshift.entities import (
    NodeResources,
    OCPCluster,
    OCPError,
    OCPNode,
    OCPProject,
)

logger = getLogger(__name__)


def catch_k8s_exception(fn):  # pylint: disable=invalid-name
    """Capture Kubernetes exception and reraise as OCPError."""

    @wraps(fn)
    def _decorator(*args, **kwargs):
        _normalize_kwargs(kwargs)
        try:
            return fn(*args, **kwargs)
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
        configuration: Configuration,
        ssl_verify: bool = True,
    ):
        """Initialize OpenShiftApi."""
        configuration.verify_ssl = ssl_verify
        self._api_client = ApiClient(configuration=configuration)
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
    def from_auth_token(
        cls, *, host, protocol, port, auth_token, ssl_verify: bool = True
    ):
        """Initialize OpenShiftApi with auth token."""
        kube_config_object = Configuration(
            host=f"{protocol}://{host}:{port}",
            api_key={"authorization": f"bearer {auth_token}"},
        )
        return cls(configuration=kube_config_object, ssl_verify=ssl_verify)

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
        except Exception:  # pylint: disable=broad-except
            if raise_exception:
                raise
            logger.exception("Got an unexpected exception. Check system logs.")
            return False
        return True

    def retrieve_projects(self, **kwargs) -> List[OCPProject]:
        """Retrieve projects/namespaces under OCP host."""
        project_list = []
        for project in self._list_projects(**kwargs).items:
            ocp_project = self._init_ocp_project(project)
            project_list.append(ocp_project)
        return project_list

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

    @catch_k8s_exception
    def _list_projects(self, **kwargs):
        return self._namespace_api.get(**kwargs)

    @catch_k8s_exception
    def _list_nodes(self, **kwargs):
        return self._node_api.get(**kwargs)

    @catch_k8s_exception
    def _list_clusters(self, **kwargs):
        return self._cluster_api.get(**kwargs)

    def _init_ocp_project(self, raw_project) -> OCPProject:
        ocp_project = OCPProject(
            name=raw_project.metadata.name,
            labels=raw_project.metadata.labels,
        )
        return ocp_project

    def _init_ocp_nodes(self, node) -> OCPNode:
        ocp_nodes = OCPNode(
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
        return ocp_nodes

    def _init_cluster(self, cluster) -> OCPCluster:
        ocp_cluster = OCPCluster(
            uuid=cluster["spec"]["clusterID"],
            version=cluster["status"]["desired"]["version"],
        )
        return ocp_cluster
