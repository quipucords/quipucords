"""Tests for api.deployments_report.tasks."""

import logging
from pathlib import Path

import pytest

from api.aggregate_report.model import get_aggregate_report_by_report_id
from api.deployments_report.tasks import (
    generate_and_save_cached_csv,
    generate_cached_fingerprints,
)
from api.models import Report
from tests.factories import DeploymentReportFactory
from utils.misc import is_valid_cache_file


@pytest.mark.django_db
def test_generate_cached_fingerprints():
    """Test generate_cached_fingerprints generates the file and updates the model."""
    deployments_report = DeploymentReportFactory.create(number_of_fingerprints=1)
    report = Report.objects.get(deployment_report=deployments_report)
    assert is_valid_cache_file(deployments_report.cached_fingerprints_file_path)
    old_cached_fingerprints = deployments_report.cached_fingerprints
    old_aggregate_report = get_aggregate_report_by_report_id(report.id)
    for _ in range(3):  # to verify repeated regens do not have unexpected side effects
        Path(deployments_report.cached_fingerprints_file_path).unlink()
        assert not is_valid_cache_file(deployments_report.cached_fingerprints_file_path)
        assert generate_cached_fingerprints(deployments_report.id)
        deployments_report.refresh_from_db()
        assert deployments_report.cached_fingerprints_file_path is not None
        assert is_valid_cache_file(deployments_report.cached_fingerprints_file_path)
        new_cached_fingerprints = deployments_report.cached_fingerprints
        assert new_cached_fingerprints == old_cached_fingerprints
        new_aggregate_report = get_aggregate_report_by_report_id(report.id)
        assert new_aggregate_report == old_aggregate_report


@pytest.mark.django_db
def test_generate_cached_fingerprints_failure(caplog):
    """Test generate_cached_fingerprints logs and suppresses unexpected exceptions."""
    caplog.set_level(logging.ERROR)
    deployments_report = DeploymentReportFactory.create(number_of_fingerprints=1)
    assert is_valid_cache_file(deployments_report.cached_fingerprints_file_path)
    deployments_report_id = deployments_report.id
    deployments_report.delete()
    assert not generate_cached_fingerprints(deployments_report_id)
    assert f"DeploymentsReport {deployments_report_id}" in caplog.messages[0]
    assert "DeploymentsReport matching query does not exist." in caplog.messages[0]


@pytest.mark.django_db
def test_generate_and_save_cached_csv():
    """Test generate_and_save_cached_csv generates the file and updates the model."""
    deployments_report = DeploymentReportFactory.create(number_of_fingerprints=1)
    assert not is_valid_cache_file(deployments_report.cached_csv_file_path)
    assert generate_and_save_cached_csv(deployments_report.id)
    deployments_report.refresh_from_db()
    assert deployments_report.cached_csv_file_path is not None
    assert is_valid_cache_file(deployments_report.cached_csv_file_path)


@pytest.mark.django_db
def test_generate_and_save_cached_csv_failure(mocker, caplog):
    """Test generate_and_save_cached_csv logs and suppresses unexpected exceptions."""
    caplog.set_level(logging.ERROR)
    deployments_report = DeploymentReportFactory.create(number_of_fingerprints=1)
    mock_build = mocker.patch("api.deployments_report.view.build_cached_json_report")
    message = "Nobody expects the Spanish Inquisition!"
    mock_build.side_effect = Exception(message)
    assert not generate_and_save_cached_csv(deployments_report.id)
    assert f"DeploymentsReport {deployments_report.id}" in caplog.messages[0]
    assert message in caplog.messages[0]
