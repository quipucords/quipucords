"""Test Ansible InspectTaskRunner."""

from unittest.mock import patch

import pytest

from api.models import ScanTask
from constants import DataSources
from scanner.ansible.exceptions import AnsibleApiDetectionError
from scanner.ansible.inspect import InspectTaskRunner
from scanner.ansible.runner import AnsibleTaskRunner
from scanner.exceptions import ScanFailureError
from tests.factories import CredentialFactory, ScanTaskFactory


@pytest.fixture
def scan_task():
    """Return a ScanTask for testing."""
    inspect_task = ScanTaskFactory(
        source__source_type=DataSources.ANSIBLE,
        source__hosts=["1.2.3.4"],
        source__port=4321,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
        sequence_number=1,
    )
    return inspect_task


@pytest.fixture
def mock_client(mocker):
    """Return a mocked Ansible client."""
    return mocker.patch.object(AnsibleTaskRunner, "get_client")


@pytest.fixture
def test_api_endpoints():
    """Return a mocked set of Ansible API endpoints."""
    return InspectTaskRunner.AAP_ENDPOINTS(
        me="/api/test/v2/me",
        ping="/api/test/v2/ping",
        hosts="/api/test/v2/hosts",
        jobs="/api/test/v2/jobs",
    )


@pytest.mark.django_db
def test_detect_ansible_endpoints_does_not_requery_api(
    mocker, mock_client, test_api_endpoints, scan_task: ScanTask
):
    """Test Detecting Ansible endpoints does not re-query API."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client
    mocker.patch.object(
        runner, "inspect", return_value=[runner.success_message, ScanTask.COMPLETED]
    )
    runner.endpoints = test_api_endpoints
    runner._detect_ansible_endpoints()
    assert not mock_client.assert_called_once()
    assert runner.endpoints.me == "/api/test/v2/me"


@pytest.mark.django_db
def test_check_connection_handles_api_detection_error(
    mocker, mock_client, test_api_endpoints, scan_task: ScanTask
):
    """Test that check_connection handles API detection errors."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client
    runner._detect_ansible_endpoints = mocker.Mock(side_effect=AnsibleApiDetectionError)
    mocker.patch.object(
        runner, "inspect", return_value=[runner.success_message, ScanTask.COMPLETED]
    )
    runner.endpoints = test_api_endpoints
    failure_message, status = runner.check_connection()
    assert not mock_client.assert_called_once()
    assert status == ScanTask.FAILED


@pytest.mark.django_db
def test_get_connection_info_with_vault_credential():
    """Test _get_connection_info fetches auth_token from Vault."""
    cred = CredentialFactory(
        cred_type=DataSources.ANSIBLE,
        vault_secret_path="vault/dev/aap-token",
        vault_mount_point="discovery",
        vault_secret_key="auth_token",
    )
    scan_task = ScanTaskFactory(
        source__credentials=[cred],
        source__source_type=DataSources.ANSIBLE,
        source__hosts=["10.0.0.1"],
        source__port=443,
    )

    with patch(
        "scanner.ansible.runner.read_vault_secret",
        return_value="vault-fetched-token",
    ) as mock_read:
        conn_info = AnsibleTaskRunner._get_connection_info(scan_task)

    mock_read.assert_called_once_with(cred)
    assert conn_info["auth_token"] == "vault-fetched-token"
    assert "username" not in conn_info
    assert "password" not in conn_info


@pytest.mark.django_db
def test_get_connection_info_vault_failure_propagates():
    """Test _get_connection_info propagates ScanFailureError from Vault."""
    cred = CredentialFactory(
        cred_type=DataSources.ANSIBLE,
        vault_secret_path="vault/dev/aap-token",
        vault_mount_point="discovery",
        vault_secret_key="auth_token",
    )
    scan_task = ScanTaskFactory(
        source__credentials=[cred],
        source__source_type=DataSources.ANSIBLE,
        source__hosts=["10.0.0.1"],
        source__port=443,
    )

    with patch(
        "scanner.ansible.runner.read_vault_secret",
        side_effect=ScanFailureError("Vault unreachable"),
    ):
        with pytest.raises(ScanFailureError, match="Vault unreachable"):
            AnsibleTaskRunner._get_connection_info(scan_task)
