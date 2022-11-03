# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Test OpenShiftTaskRunner."""

import pytest

from scanner.openshift.task import OpenShiftTaskRunner
from tests.factories import CredentialFactory, ScanTaskFactory


@pytest.fixture
def patched_ocp_client(mocker):
    """OpenShiftApi mocked."""
    _api_client = mocker.patch("scanner.openshift.task.OpenShiftApi")
    yield _api_client


@pytest.mark.django_db
@pytest.mark.parametrize("auth_token", ["qwe", "zxc"])
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
def test_get_ocp_client_arguments(  # pylint: disable=too-many-arguments
    patched_ocp_client,
    auth_token,
    host,
    port,
    source_kwargs,
    expected_protocol,
    ssl_verify,
):
    """Test if OpenShiftApi is properly receiving its initialization arguments."""
    cred = CredentialFactory(auth_token=auth_token, cred_type="openshift")
    scan_task = ScanTaskFactory(
        source__credentials=[cred],
        source__source_type="openshift",
        source__hosts=f'["{host}"]',
        source__port=port,
        **source_kwargs,
    )
    OpenShiftTaskRunner.get_ocp_client(scan_task)
    expected_client_kwargs = {
        "auth_token": auth_token,
        "host": host,
        "port": port,
        "protocol": expected_protocol,
        "ssl_verify": ssl_verify,
    }
    patched_ocp_client.from_auth_token.assert_called_once()
    assert patched_ocp_client.from_auth_token.call_args.kwargs == expected_client_kwargs
