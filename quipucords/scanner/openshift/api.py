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

from scanner.openshift.entities import OCPCluster, OCPDeployment, OCPError, OCPProject

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

    def retrieve_projects(self, retrieve_all=True, **kwargs) -> List[OCPProject]:
        """Retrieve projects/namespaces under OCP host."""
        project_list = []
        for project in self._list_projects(**kwargs).items:
            ocp_project = self._init_ocp_project(project, retrieve_all=retrieve_all)
            project_list.append(ocp_project)
        return project_list

    def retrieve_cluster(self, **kwargs) -> OCPCluster:
        """Retrieve cluster under OCP host."""
        clusters = self._list_clusters(**kwargs).items
        assert len(clusters) == 1, "More than one cluster in cluster API"
        cluster_entity = self._init_cluster(clusters[0])
        return cluster_entity

    def retrieve_deployments(self, project_name, **kwargs) -> List[OCPDeployment]:
        """Retrieve deployments under project 'project_name'."""
        deployments_raw = self._list_deployments(project_name, **kwargs)
        deployments_list = []
        for dep in deployments_raw.items:
            ocp_deployment = self._init_ocp_deployment(dep)
            deployments_list.append(ocp_deployment)
        return deployments_list

    @cached_property
    def _core_api(self):
        return CoreV1Api(api_client=self._api_client)

    @cached_property
    def _apps_api(self):
        return AppsV1Api(api_client=self._api_client)

    @cached_property
    def _cluster_api(self):
        return self._dynamic_client.resources.get(
            api_version="config.openshift.io/v1", kind="ClusterVersion"
        )

    @catch_k8s_exception
    @wraps(CoreV1Api.list_namespace)
    def _list_projects(self, **kwargs):
        return self._core_api.list_namespace(**kwargs)

    @catch_k8s_exception
    def _list_clusters(self, **kwargs):
        return self._cluster_api.get(**kwargs)

    @catch_k8s_exception
    @wraps(AppsV1Api.list_namespaced_deployment)
    def _list_deployments(self, namespace, **kwargs):
        return self._apps_api.list_namespaced_deployment(namespace, **kwargs)

    def _init_ocp_project(self, raw_project, retrieve_all=True) -> OCPProject:
        ocp_project = OCPProject(
            name=raw_project.metadata.name,
            labels=raw_project.metadata.labels,
        )
        if retrieve_all:
            self.add_deployments_to_project(ocp_project)
        return ocp_project

    def _init_cluster(self, cluster) -> OCPCluster:
        ocp_cluster = OCPCluster(
            uuid=cluster["spec"]["clusterID"],
            version=cluster["status"]["desired"]["version"],
        )
        return ocp_cluster

    def add_deployments_to_project(self, ocp_project, **kwargs):
        """Retrieve deployments and add to OCPProject."""
        try:
            deployments = self.retrieve_deployments(ocp_project.name, **kwargs)
            ocp_project.deployments = deployments
        except OCPError as error:
            ocp_project.errors["deployments"] = error

    def _init_ocp_deployment(self, raw_deployment):
        def _getter(obj, name, default_value=None):
            return getattr(obj, name, default_value) or default_value

        metadata = _getter(raw_deployment, "metadata")
        template_spec = raw_deployment.spec.template.spec
        container_images = [c.image for c in _getter(template_spec, "containers", [])]
        init_container_images = [
            c.image for c in _getter(template_spec, "init_containers", [])
        ]

        return OCPDeployment(
            name=_getter(metadata, "name"),
            labels=_getter(metadata, "labels", {}),
            container_images=container_images,
            init_container_images=init_container_images,
        )
