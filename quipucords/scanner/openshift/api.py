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

from scanner.openshift.entities import OCPDeployment, OCPError, OCPProject

logger = getLogger(__name__)


def catch_k8s_exception(fn):  # pylint: disable=invalid-name
    """Capture Kubernetes exception and reraise as OCPError."""

    @wraps(fn)
    def _decorator(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ApiException as api_exception:
            ocp_error = OCPError.from_api_exception(api_exception)
            raise ocp_error from api_exception

    return _decorator


class OpenShiftApi:
    """OpenShift interface for Quipucords."""

    def __init__(self, configuration: Configuration):
        """Initialize OpenShiftApi."""
        self._api_client = ApiClient(configuration=configuration)

    @classmethod
    def from_auth_token(cls, *, host, protocol, port, auth_token):
        """Initialize OpenShiftApi with auth token."""
        kube_config_object = Configuration(
            host=f"{protocol}://{host}:{port}",
            api_key={"authorization": f"bearer {auth_token}"},
        )
        return cls(configuration=kube_config_object)

    def can_connect(self):
        """Check if it's possible to connect to OCP host."""
        try:
            # call a lightweight endpoint just to check if we can
            # stablish a connection
            self._core_api.get_api_resources()
        except ApiException as err:
            logger.exception("Unable to connect to OCP/K8S api (status=%s)", err.status)
            return False
        return True

    def retrieve_projects(self) -> List[OCPProject]:
        """Retrieve projects/namespaces under OCP host."""
        project_list = []
        for project in self._list_projects().items:
            ocp_project = self._init_ocp_project(project)
            project_list.append(ocp_project)
        return project_list

    def retrieve_deployments(self, project_name) -> List[OCPDeployment]:
        """Retrieve deployments under project 'project_name'."""
        deployments_raw = self._list_deployments(project_name)
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

    @catch_k8s_exception
    @wraps(CoreV1Api.list_namespace)
    def _list_projects(self, **kwargs):
        return self._core_api.list_namespace(**kwargs)

    @catch_k8s_exception
    @wraps(AppsV1Api.list_namespaced_deployment)
    def _list_deployments(self, namespace, **kwargs):
        return self._apps_api.list_namespaced_deployment(namespace, **kwargs)

    def _init_ocp_project(self, raw_project) -> OCPProject:
        ocp_project = OCPProject(
            name=raw_project.metadata.name,
            labels=raw_project.metadata.labels,
        )
        self._add_deployments_to_project(ocp_project)
        return ocp_project

    def _add_deployments_to_project(self, ocp_project):
        try:
            deployments = self.retrieve_deployments(ocp_project.name)
            ocp_project.deployments.extend(deployments)
        except OCPError as error:
            ocp_project.errors["deployments"] = error

    def _init_ocp_deployment(self, raw_deployment):
        container_images = [
            c.image for c in raw_deployment.spec.template.spec.containers
        ]
        init_container_images = [
            c.image for c in (raw_deployment.spec.template.spec.init_containers or [])
        ]

        return OCPDeployment(
            name=raw_deployment.metadata.name,
            labels=raw_deployment.metadata.labels,
            container_images=container_images,
            init_container_images=init_container_images,
        )
