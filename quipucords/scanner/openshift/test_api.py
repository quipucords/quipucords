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
from pathlib import Path

import httpretty
import pytest

from scanner.openshift.api import OpenShiftApi
from scanner.openshift.entities import OCPDeployment, OCPError, OCPProject
from tests.asserts import assert_elements_type

FULL_ACCESS_PROJECT = "awesome_project"
FORBIDDEN_PROJECT = "forbidden_project"
OPENSHIFT_HOST = "fake.openshift.host"
OPENSHIFT_PORT = 9876
OPENSHIFT_TOKEN = "<API TOKEN>"
OPENSHIFT_PROTOCOL = "https"


def data_path(filename) -> Path:
    """Path object for testing data."""
    return Path(__file__).parent / "test_data" / filename


class TestData:
    """
    Constants holding path for OCP Rest Api responses.

    They are based on real data and then were tweaked/reduced for testing purposes.
    """

    API_RESOURCE_LIST = data_path("api_resource_list.json")
    # deployments of "awesome_project", which we have at least read access
    DEPLOYMENTS_VALID = data_path("deployment_list_valid.json")
    # deployments response for "forbidden_project", which we can't access
    FORBIDDEN_DEPLOYMENT = data_path("forbidden_deployment.json")
    NAMESPACE_LIST = data_path("namespace_list.json")
    UNAUTHORIZED_RESPONSE = data_path("unauthorized_response.json")


def patch_ocp_api(path, **kwargs):
    """Shortcut for patching ocp requests."""
    httpretty.register_uri(
        httpretty.GET,
        f"{OPENSHIFT_PROTOCOL}://{OPENSHIFT_HOST}:{OPENSHIFT_PORT}/{path}",
        **kwargs,
    )


@pytest.fixture
def ocp_client():
    """OCP client for testing."""
    return OpenShiftApi.from_auth_token(
        auth_token=OPENSHIFT_TOKEN,
        host=OPENSHIFT_HOST,
        port=OPENSHIFT_PORT,
        protocol=OPENSHIFT_PROTOCOL,
    )


def test_from_auth_token(mocker):
    """Test factory method from_auth_token."""
    patched_kube_config = mocker.patch("scanner.openshift.api.Configuration")
    patched_api_client = mocker.patch("scanner.openshift.api.ApiClient")
    client = OpenShiftApi.from_auth_token(
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
    assert (  # pylint: disable=protected-access
        client._api_client == patched_api_client()
    )


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


@httpretty.activate
@pytest.mark.parametrize(
    "method,args,path",
    [
        (
            "retrieve_projects",
            (),
            "api/v1/namespaces",
        ),
        (
            "retrieve_deployments",
            ("some_project",),
            "apis/apps/v1/namespaces/some_project/deployments",
        ),
    ],
)
def test_unauthorized_error(ocp_client, method, args, path):
    """Test unauthorized error on public methods."""
    patch_ocp_api(
        path,
        body=TestData.UNAUTHORIZED_RESPONSE.read_text(),
        status=401,
    )
    with pytest.raises(OCPError) as exc_info:
        getattr(ocp_client, method)(*args)
    assert exc_info.value.status == 401
    assert exc_info.value.message == "Unauthorized"
    assert exc_info.value.reason == "Unauthorized"


@httpretty.activate
def test_retrieve_deployments_succesful(ocp_client: OpenShiftApi):
    """Test retrieving deployments from an project with full access."""
    patch_ocp_api(
        f"apis/apps/v1/namespaces/{FULL_ACCESS_PROJECT}/deployments",
        body=TestData.DEPLOYMENTS_VALID.read_text(),
    )
    deployments = ocp_client.retrieve_deployments(FULL_ACCESS_PROJECT)
    assert_elements_type(deployments, OCPDeployment)

    another_app_dep, awesome_app = deployments

    assert another_app_dep.name == "another-app"
    assert another_app_dep.labels == {
        "app": "another-app",
        "label-for": "another-app-container",
    }
    assert another_app_dep.container_images == ["another-app-image:latest"]
    assert another_app_dep.init_container_images == []

    assert awesome_app.name == "awesome-app"
    assert awesome_app.labels == {
        "app": "awesome-app",
        "label-for": "awesome-app-container",
    }
    assert awesome_app.container_images == ["main-container-image:latest"]
    assert awesome_app.init_container_images == ["some-init-container-img:latest"]


@httpretty.activate
def test_retrieve_deployments_forbidden(ocp_client: OpenShiftApi):
    """Test retrieving deployments from an project without access."""
    patch_ocp_api(
        f"apis/apps/v1/namespaces/{FORBIDDEN_PROJECT}/deployments",
        body=TestData.FORBIDDEN_DEPLOYMENT.read_text(),
        status=403,
    )
    with pytest.raises(OCPError) as exc_info:
        ocp_client.retrieve_deployments(FORBIDDEN_PROJECT)

    ocp_error = exc_info.value

    assert ocp_error.reason == "Forbidden"
    assert ocp_error.status == 403
    assert ocp_error.message == (
        'deployments.apps is forbidden: User "ocp-user" cannot list resource '
        f'"deployments" in API group "apps" in the namespace "{FORBIDDEN_PROJECT}"'
    )


@httpretty.activate
def test_retrieve_projects(ocp_client: OpenShiftApi):
    """Test retrieving projects."""
    patch_ocp_api(
        "api/v1/namespaces",
        body=TestData.NAMESPACE_LIST.read_text(),
    )
    patch_ocp_api(
        "apis/apps/v1/namespaces/awesome_project/deployments",
        body=TestData.DEPLOYMENTS_VALID.read_text(),
    )
    patch_ocp_api(
        "apis/apps/v1/namespaces/forbidden_project/deployments",
        status=403,
        body=TestData.FORBIDDEN_DEPLOYMENT.read_text(),
    )

    projects = ocp_client.retrieve_projects()
    assert len(projects) == 2
    assert_elements_type(projects, OCPProject)

    full_access_project, forbidden_project = projects

    assert full_access_project.deployments
    assert_elements_type(full_access_project.deployments, OCPDeployment)
    assert not full_access_project.errors

    assert not forbidden_project.deployments
    assert forbidden_project.errors
    assert_elements_type(forbidden_project.errors.values(), OCPError)
