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
