"""Test Ansible InspectTaskRunner."""

from unittest.mock import patch

import pytest
from django.test import override_settings
from requests import RequestException

from api.inspectresult.model import InspectResult
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
        host_metrics="/api/test/v2/host_metrics",
    )


@pytest.fixture
def test_api_endpoints_without_host_metrics():
    """Return AAP endpoints without host_metrics (older AAP versions)."""
    return InspectTaskRunner.AAP_ENDPOINTS(
        me="/api/test/v2/me",
        ping="/api/test/v2/ping",
        hosts="/api/test/v2/hosts",
        jobs="/api/test/v2/jobs",
        host_metrics=None,
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


@pytest.mark.django_db
def test_get_unique_hosts_from_metrics(mocker, mock_client, scan_task):
    """Test get_unique_hosts_from_metrics successfully retrieves hosts."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client

    # Mock the endpoint
    runner.endpoints = InspectTaskRunner.AAP_ENDPOINTS(
        me="/api/v2/me",
        ping="/api/v2/ping",
        hosts="/api/v2/hosts",
        jobs="/api/v2/jobs",
        host_metrics="/api/v2/host_metrics",
    )

    # Mock the paginated results
    mock_metrics = [
        {"hostname": "host1.example.com", "deleted": False},
        {"hostname": "host2.example.com", "deleted": True},
        {"hostname": "host3.example.com", "deleted": False},
        {"hostname": "", "deleted": False},  # Should be filtered out
        {"hostname": None, "deleted": False},  # Should be filtered out
    ]

    mock_client.get_paginated_results = mocker.Mock(return_value=iter(mock_metrics))

    result = runner.get_unique_hosts_from_metrics()

    assert result == {"host1.example.com", "host2.example.com", "host3.example.com"}
    assert "" not in result
    assert None not in result


@pytest.mark.django_db
def test_inspect_uses_host_metrics_when_available(mocker, mock_client, scan_task):
    """Test that inspect() uses host_metrics when endpoint is available."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client

    # Mock endpoints with host_metrics available
    runner.endpoints = InspectTaskRunner.AAP_ENDPOINTS(
        me="/api/v2/me",
        ping="/api/v2/ping",
        hosts="/api/v2/hosts",
        jobs="/api/v2/jobs",
        host_metrics="/api/v2/host_metrics",
    )

    # Mock the various methods
    mocker.patch.object(runner, "get_instance_details", return_value={"version": "2.4"})
    mocker.patch.object(runner, "get_hosts", return_value=[{"name": "localhost"}])
    mocker.patch.object(
        runner,
        "get_unique_hosts_from_metrics",
        return_value={"host1.example.com", "host2.example.com"},
    )
    mocker.patch.object(runner, "save_results")

    # Ensure setting is enabled
    with override_settings(QUIPUCORDS_AAP_USE_HOST_METRICS=True):
        runner.inspect()

    # Verify host_metrics was called
    runner.get_unique_hosts_from_metrics.assert_called_once()

    # Verify results were saved with unique_hosts
    call_args = runner.save_results.call_args
    assert call_args is not None
    results = call_args[0][1]  # Second argument to save_results
    assert "unique_hosts" in results
    assert set(results["unique_hosts"]) == {"host1.example.com", "host2.example.com"}


@pytest.mark.django_db
def test_inspect_falls_back_to_jobs_when_host_metrics_unavailable(
    mocker, mock_client, scan_task
):
    """Test that inspect() falls back to jobs when host_metrics is not available."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client

    # Mock endpoints WITHOUT host_metrics (older AAP)
    runner.endpoints = InspectTaskRunner.AAP_ENDPOINTS(
        me="/api/v2/me",
        ping="/api/v2/ping",
        hosts="/api/v2/hosts",
        jobs="/api/v2/jobs",
        host_metrics=None,
    )

    # Mock the various methods
    mocker.patch.object(runner, "get_instance_details", return_value={"version": "2.4"})
    mocker.patch.object(runner, "get_hosts", return_value=[{"name": "localhost"}])
    mocker.patch.object(
        runner,
        "get_jobs",
        return_value={
            "job_ids": [1, 2, 3],
            "unique_hosts": {"host1.example.com", "host2.example.com"},
        },
    )
    mocker.patch.object(runner, "save_results")

    with override_settings(QUIPUCORDS_AAP_USE_HOST_METRICS=True):
        runner.inspect()

    # Verify get_jobs was called as fallback
    runner.get_jobs.assert_called_once()

    # Verify results were saved with unique_hosts
    call_args = runner.save_results.call_args
    assert call_args is not None
    results = call_args[0][1]
    assert "unique_hosts" in results


@pytest.mark.django_db
def test_inspect_respects_feature_flag_disabled(mocker, mock_client, scan_task):
    """Test that inspect() respects QUIPUCORDS_AAP_USE_HOST_METRICS=False."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client

    # Mock endpoints with host_metrics available
    runner.endpoints = InspectTaskRunner.AAP_ENDPOINTS(
        me="/api/v2/me",
        ping="/api/v2/ping",
        hosts="/api/v2/hosts",
        jobs="/api/v2/jobs",
        host_metrics="/api/v2/host_metrics",
    )

    # Mock the various methods
    mocker.patch.object(runner, "get_instance_details", return_value={"version": "2.4"})
    mocker.patch.object(runner, "get_hosts", return_value=[{"name": "localhost"}])
    mocker.patch.object(
        runner,
        "get_jobs",
        return_value={"job_ids": [1, 2], "unique_hosts": {"host1.example.com"}},
    )
    mocker.patch.object(runner, "get_unique_hosts_from_metrics", return_value=set())
    mocker.patch.object(runner, "save_results")

    # Disable the feature flag
    with override_settings(QUIPUCORDS_AAP_USE_HOST_METRICS=False):
        runner.inspect()

    # Verify get_jobs was called (not host_metrics)
    runner.get_jobs.assert_called_once()
    runner.get_unique_hosts_from_metrics.assert_not_called()


@pytest.mark.django_db
def test_inspect_generates_comparison_with_host_metrics(mocker, mock_client, scan_task):
    """Test that inspect() generates comparison data with host_metrics endpoint."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client

    runner.endpoints = InspectTaskRunner.AAP_ENDPOINTS(
        me="/api/v2/me",
        ping="/api/v2/ping",
        hosts="/api/v2/hosts",
        jobs="/api/v2/jobs",
        host_metrics="/api/v2/host_metrics",
    )

    # Mock hosts in current inventory
    mocker.patch.object(
        runner,
        "get_hosts",
        return_value=[
            {"name": "current1.example.com"},
            {"name": "current2.example.com"},
            {"name": "current3.example.com"},
        ],
    )

    # Mock hosts that have run automation (includes deleted hosts)
    mocker.patch.object(
        runner,
        "get_unique_hosts_from_metrics",
        return_value={
            "current1.example.com",  # in both
            "current2.example.com",  # in both
            "deleted1.example.com",  # only in host_metrics (deleted)
            "deleted2.example.com",  # only in host_metrics (deleted)
        },
    )

    mocker.patch.object(runner, "get_instance_details", return_value={"version": "2.5"})
    mocker.patch.object(runner, "save_results")

    with override_settings(QUIPUCORDS_AAP_USE_HOST_METRICS=True):
        runner.inspect()

    # Verify comparison was generated
    call_args = runner.save_results.call_args
    assert call_args is not None
    results = call_args[0][1]  # Second argument to save_results

    assert "comparison" in results
    comparison = results["comparison"]

    # Verify comparison statistics
    assert "hosts_in_inventory" in comparison
    assert "hosts_only_in_jobs" in comparison
    assert "number_of_hosts_in_inventory" in comparison
    assert "number_of_hosts_only_in_jobs" in comparison

    # Verify counts
    # current1, current2, current3
    assert comparison["number_of_hosts_in_inventory"] == 3
    assert comparison["number_of_hosts_only_in_jobs"] == 2  # deleted1, deleted2

    # Verify sets
    assert comparison["hosts_in_inventory"] == {
        "current1.example.com",
        "current2.example.com",
        "current3.example.com",
    }
    assert comparison["hosts_only_in_jobs"] == {
        "deleted1.example.com",
        "deleted2.example.com",
    }


@pytest.mark.django_db
def test_inspect_comparison_not_generated_on_failure(mocker, mock_client, scan_task):
    """Test that inspect() does not generate comparison when inspection fails."""
    runner = InspectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    runner.client = mock_client

    runner.endpoints = InspectTaskRunner.AAP_ENDPOINTS(
        me="/api/v2/me",
        ping="/api/v2/ping",
        hosts="/api/v2/hosts",
        jobs="/api/v2/jobs",
        host_metrics="/api/v2/host_metrics",
    )

    # Make get_instance_details fail
    mocker.patch.object(
        runner,
        "get_instance_details",
        side_effect=RequestException("Connection failed"),
    )
    mocker.patch.object(runner, "get_hosts", return_value=[])
    mocker.patch.object(runner, "get_unique_hosts_from_metrics", return_value=set())
    mocker.patch.object(runner, "save_results")

    with override_settings(QUIPUCORDS_AAP_USE_HOST_METRICS=True):
        runner.inspect()

    # Verify comparison was NOT generated (inspection failed)
    call_args = runner.save_results.call_args
    assert call_args is not None
    status = call_args[0][0]  # First argument to save_results
    results = call_args[0][1]  # Second argument to save_results

    assert status == InspectResult.FAILED
    assert "comparison" not in results
