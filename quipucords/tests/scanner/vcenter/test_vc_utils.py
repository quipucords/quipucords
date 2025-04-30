"""Test the vcenter utils."""

from unittest.mock import ANY, Mock, patch

import pytest

from api.models import Credential, ScanTask, Source
from scanner.vcenter.utils import vcenter_connect
from tests.scanner.test_util import create_scan_job


def create_scan_task(
    source_disable_ssl: bool, source_ssl_cert_verify: bool
) -> ScanTask:
    """Create custom ScanTask for testing."""
    cred = Credential.objects.create(
        name="cred1",
        username="username",
        password="password",
        become_password=None,
        ssh_keyfile=None,
    )
    source = Source.objects.create(
        name="source1",
        port=22,
        hosts=["1.2.3.4"],
        disable_ssl=source_disable_ssl,
        ssl_cert_verify=source_ssl_cert_verify,
        ssl_protocol=None,
    )
    source.credentials.add(cred)

    scan_job, scan_task = create_scan_job(source)
    return scan_task


@pytest.mark.django_db
@pytest.mark.parametrize(
    "disable_ssl,ssl_cert_verify",
    [[True, True], [False, False], [False, None], [True, False], [False, True]],
)
def test_vcenter_connect(disable_ssl, ssl_cert_verify):
    """Test the SmartConnect connection arguments."""
    scan_task = create_scan_task(disable_ssl, ssl_cert_verify)
    expected_connect_kwargs = {
        "host": ANY,
        "user": ANY,
        "pwd": ANY,
        "port": ANY,
        "httpProxyHost": None,
        "httpProxyPort": None,
    }
    if disable_ssl:
        expected_connect_kwargs["disableSslCertValidation"] = True
    elif ssl_cert_verify is not None:
        expected_connect_kwargs["sslContext"] = ANY

    mock_vcenter = Mock()
    with patch(
        "scanner.vcenter.utils.SmartConnect", return_value=mock_vcenter
    ) as mock_smart_connect:
        vcenter = vcenter_connect(scan_task)
        assert mock_vcenter == vcenter
        mock_smart_connect.assert_called_once_with(**expected_connect_kwargs)


@pytest.mark.django_db
def test_vcenter_connect_with_proxy():
    """Test that proxy information is passed correctly to SmartConnect."""
    scan_task = create_scan_task(source_disable_ssl=False, source_ssl_cert_verify=True)
    scan_task.source.proxy_url = "http://proxy.example.com:8888"
    scan_task.source.save()

    mock_vcenter = Mock()
    with patch(
        "scanner.vcenter.utils.SmartConnect", return_value=mock_vcenter
    ) as mock_connect:
        vcenter = vcenter_connect(scan_task)
        assert mock_vcenter == vcenter
        mock_connect.assert_called_once()
        kwargs = mock_connect.call_args.kwargs
        assert kwargs["httpProxyHost"] == "proxy.example.com"
        assert kwargs["httpProxyPort"] == 8888


@pytest.mark.django_db
def test_vcenter_connect_with_invalid_proxy_format():
    """Test that invalid proxy format does not set proxy values."""
    scan_task = create_scan_task(source_disable_ssl=False, source_ssl_cert_verify=True)
    scan_task.source.proxy_url = "proxyexample"
    scan_task.source.save()

    mock_vcenter = Mock()
    with patch(
        "scanner.vcenter.utils.SmartConnect", return_value=mock_vcenter
    ) as mock_connect:
        vcenter = vcenter_connect(scan_task)
        assert mock_vcenter == vcenter
        kwargs = mock_connect.call_args.kwargs
        assert kwargs["httpProxyHost"] is None
        assert kwargs["httpProxyPort"] is None
