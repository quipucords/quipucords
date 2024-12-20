"""Test SatelliteInterface._prepare_and_process_hosts when Celery is enabled."""

from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from api.scantask.model import ScanTask
from constants import DataSources
from scanner.satellite import six
from tests.factories import ScanTaskFactory


def fake_six_request_host_details(  # noqa: PLR0913
    *,
    scan_task_id,
    logging_options,
    host_id,
    host_name,
    fields_url,
    subs_url,
    request_options,
):
    """Generate a fake response for a call to Satellite 6 style request_host_details.

    This function's signature must match six._request_host_details's signature.
    """
    return {
        "unique_name": f"{host_id}-unique_name",
        "system_inspection_result": f"{host_id}-system_inspection_result",
        "host_fields_response": f"{host_id}-host_fields_response",
        "host_subscriptions_response": f"{host_id}-host_subscriptions_response",
    }


def fake_prepare_hosts(hosts, *args, **kwargs) -> list[dict]:
    """Prepare a minimally-populated object to mimic SatelliteSix.prepare_hosts."""
    return [
        {
            "scan_task_id": None,
            "logging_options": None,
            "host_id": host["id"],
            "host_name": host["name"],
            "fields_url": None,
            "subs_url": None,
            "request_options": {},
        }
        for host in hosts
    ]


@pytest.fixture
def mock__request_host_details():
    """Patch six._request_host_details to override Celery task implementation."""
    with patch.object(six, "_request_host_details") as _request_host_details:
        _request_host_details.side_effect = fake_six_request_host_details
        yield _request_host_details


@pytest.fixture
def mock_prepare_hosts():
    """Patch SatelliteSix.prepare_hosts to return fake prepared hosts test data."""
    with patch.object(six.SatelliteSix, "prepare_hosts") as prepare_hosts:
        prepare_hosts.side_effect = fake_prepare_hosts
        yield prepare_hosts


@pytest.fixture
def inspect_scan_job():
    """Prepare an "inspect" type ScanJob.

    Important note: This does not have the complete set of related objects for a real
    inspect job, but it has sufficient data for just what this module is testing.
    """
    connect_task = ScanTaskFactory(
        source__source_type=DataSources.SATELLITE,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
        status=ScanTask.PENDING,
        job__scan_type=ScanTask.SCAN_TYPE_INSPECT,
        job__status=ScanTask.PENDING,
    )
    return connect_task.job


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db(transaction=True)
def test__prepare_and_process_hosts_using_celery(
    mock_prepare_hosts, mock__request_host_details, celery_worker, inspect_scan_job
):
    """Test SatelliteInterface._prepare_and_process_hosts Celery task interaction.

    This test uses the SatelliteSixV2 implementation of SatelliteInterface, but the same
    logic should also apply to SatelliteSixV1 because the code relevant to
    this test's behavior lives in the parent SatelliteInterface class.

    We use the celery_worker fixture here to embed a live worker because we are
    interested specifically in verifying that the Celery tasks are invoked as expected.
    We patch out their inner implementations, though, because they would normally make
    external API calls.
    """
    inspect_scan_task = inspect_scan_job.tasks.first()
    satellite = six.SatelliteSixV2(inspect_scan_job, inspect_scan_task)

    hosts = [
        {"name": "host_a", "id": 1},
        {"name": "host_b", "id": 2},
        {"name": "host_c", "id": 3},
    ]

    expected_prepare_host_return = [
        # All these Nones are just to fill out the function signature.
        # Since we are patching, we do not need to supply real values for everything.
        fake_six_request_host_details(
            scan_task_id=None,
            logging_options=None,
            host_id=host["id"],
            host_name=host["name"],
            fields_url=None,
            subs_url=None,
            request_options=None,
        )
        for host in hosts
    ]

    mock_process_results = Mock()
    satellite._prepare_and_process_hosts(
        hosts, six.request_host_details, mock_process_results
    )

    mock_prepare_hosts.assert_called_once()
    assert mock__request_host_details.call_count == len(hosts)
    mock_process_results.assert_called_once_with(results=expected_prepare_host_return)
