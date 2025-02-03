"""Tests for api.deployments_report.tasks."""

import logging

import pytest

from api.deployments_report.tasks import generate_and_save_cached_csv
from tests.factories import DeploymentReportFactory
from utils.misc import is_valid_cache_file


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
    mock_build = mocker.patch("api.deployments_report.tasks.build_cached_json_report")
    message = "Nobody expects the Spanish Inquisition!"
    mock_build.side_effect = Exception(message)
    assert not generate_and_save_cached_csv(deployments_report.id)
    assert message in caplog.messages
