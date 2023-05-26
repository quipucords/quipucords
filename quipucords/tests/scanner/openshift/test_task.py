"""Test OpenShiftTaskRunner."""

import pytest

from scanner.openshift.api import OpenShiftApi
from scanner.openshift.runner import OpenShiftTaskRunner
from tests.factories import CredentialFactory, ScanTaskFactory


@pytest.fixture(autouse=True)
def _disable_k8s_clients(mocker):
    """Disable K8s clients to avoid api calls they make when initialized."""
    mocker.patch("scanner.openshift.api.ApiClient")
    mocker.patch("scanner.openshift.api.DynamicClient")


@pytest.mark.django_db
@pytest.mark.parametrize("host", ["1.2.3.4", "some.host.com"])
@pytest.mark.parametrize("port", [9999, 8888])
@pytest.mark.parametrize(
    "source_kwargs,expected_protocol,ssl_verify",
    [
        ({"source__options": None}, "https", True),
        (
            {
                "source__options__ssl_cert_verify": True,
                "source__options__disable_ssl": False,
            },
            "https",
            True,
        ),
        (
            {
                "source__options__ssl_cert_verify": False,
                "source__options__disable_ssl": False,
            },
            "https",
            False,
        ),
        (
            {
                "source__options__ssl_cert_verify": False,
                "source__options__disable_ssl": True,
            },
            "http",
            False,
        ),
        (
            {
                "source__options__ssl_cert_verify": True,
                "source__options__disable_ssl": True,
            },
            "http",
            False,
        ),
    ],
)
class TestGetOcpClient:
    """Test if OpenShiftApi is properly receiving its initialization arguments."""

    @pytest.mark.parametrize("auth_token", ["qwe", "zxc"])
    def test_with_auth_token(  # pylint: disable=too-many-arguments
        self,
        mocker,
        auth_token,
        host,
        port,
        source_kwargs,
        expected_protocol,
        ssl_verify,
    ):
        """Test OpenshiftApi.get_ocp_client receiving auth_token."""
        patched_kube_config = mocker.patch.object(OpenShiftApi, "_init_kube_config")

        cred = CredentialFactory(auth_token=auth_token, cred_type="openshift")
        scan_task = ScanTaskFactory(
            source__credentials=[cred],
            source__source_type="openshift",
            source__hosts=[host],
            source__port=port,
            **source_kwargs,
        )
        client = OpenShiftTaskRunner.get_ocp_client(scan_task)
        assert isinstance(client, OpenShiftApi)
        expected_kube_config_call = mocker.call(
            f"{expected_protocol}://{host}:{port}",
            ssl_verify=ssl_verify,
            auth_token=auth_token,
        )
        patched_kube_config.assert_called_once()
        assert patched_kube_config.call_args == expected_kube_config_call

    def test_with_user_pass(  # pylint: disable=too-many-arguments
        self,
        mocker,
        host,
        port,
        source_kwargs,
        expected_protocol,
        ssl_verify,
    ):
        """Test OpenshiftApi.get_ocp_client receiving auth_token."""
        patched_kube_config = mocker.patch(
            "scanner.openshift.api.OCPLoginConfiguration"
        )

        cred = CredentialFactory(
            cred_type="openshift", username="<USER>", password="<PASSWORD>"
        )
        scan_task = ScanTaskFactory(
            source__credentials=[cred],
            source__source_type="openshift",
            source__hosts=[host],
            source__port=port,
            **source_kwargs,
        )
        client = OpenShiftTaskRunner.get_ocp_client(scan_task)
        assert isinstance(client, OpenShiftApi)
        expected_kube_config_call = mocker.call(
            host=f"{expected_protocol}://{host}:{port}",
            ocp_username="<USER>",
            ocp_password="<PASSWORD>",
        )
        assert patched_kube_config.call_args == expected_kube_config_call
        assert patched_kube_config().verify_ssl == ssl_verify
