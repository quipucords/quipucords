"""Test the _connect function of the scanner.network.inspect module."""

from unittest.mock import Mock, patch

import pytest
from ansible_runner import AnsibleRunnerException
from django.test import override_settings

from api.models import Scan
from scanner.network.inspect import _connect
from tests.scanner.test_util import create_scan_job

pytestmark = pytest.mark.django_db  # all tests here require the database


@patch("ansible_runner.run")
def test__connect_paramiko(mock_run, network_source):
    """Test _connect use_paramiko sends arg to run."""
    mock_run.return_value.status = "successful"
    scan_job, scan_task = create_scan_job(network_source)
    _connect(
        scan_task=scan_task,
        hosts=network_source.hosts,
        result_store=Mock(),
        credential=network_source.credentials.first(),
        connection_port=network_source.port,
        forks=Scan.DEFAULT_MAX_CONCURRENCY,
        use_paramiko=True,
        ssh_keyfile=None,
    )
    mock_run.assert_called_once()
    calls = mock_run.mock_calls
    assert "--connection=paramiko" in calls[0].kwargs["cmdline"]


@patch("ansible_runner.run")
def test__connect_raises_exception_when_ansible_runner_run_fails(
    mock_run, network_source
):
    """Test ansible_runner.run exception raises AnsibleRunnerException in _connect."""
    mock_run.side_effect = Exception()
    scan_job, scan_task = create_scan_job(network_source)
    with pytest.raises(AnsibleRunnerException):
        _connect(
            scan_task=scan_task,
            hosts=network_source.hosts,
            result_store=Mock(),
            credential=network_source.credentials.first(),
            connection_port=network_source.port,
            forks=Scan.DEFAULT_MAX_CONCURRENCY,
            ssh_keyfile=None,
        )
    mock_run.assert_called_once()


@patch("ansible_runner.run")
@override_settings(ANSIBLE_LOG_LEVEL=1)
def test__connect_with_modified_ansible_log_level(mock_run, network_source):
    """Test modifying ANSIBLE_LOG_LEVEL (from default 3 to 1) sends arg to run."""
    mock_run.return_value.status = "successful"
    scan_job, scan_task = create_scan_job(network_source)
    _connect(
        scan_task=scan_task,
        hosts=network_source.hosts,
        result_store=Mock(),
        credential=network_source.credentials.first(),
        connection_port=network_source.port,
        forks=Scan.DEFAULT_MAX_CONCURRENCY,
        ssh_keyfile=None,
    )
    mock_run.assert_called_once()
    run_call = mock_run.mock_calls[0]
    assert "verbosity" in run_call.kwargs
    assert run_call.kwargs["verbosity"] == 1
