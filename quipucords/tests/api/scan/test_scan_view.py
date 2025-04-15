"""Test ScanViewSet and related v1 view functions."""

from unittest import mock

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api import messages
from api.models import InspectResult, RawFact, ScanTask, SystemConnectionResult
from tests.factories import (
    CredentialFactory,
    InspectGroupFactory,
    ScanFactory,
    ScanJobFactory,
    SourceFactory,
)
from tests.scanner.test_util import create_scan_job

pytestmark = pytest.mark.django_db  # all tests here require the database


def test_delete_scan_cascade(client_logged_in):
    """Delete a scan and its related data."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scanjob, scan_task = create_scan_job(source)

    scan = scanjob.scan
    scan_id = scan.id

    # Create a connection system result
    conn_result = scan_task.connection_result
    SystemConnectionResult.objects.create(
        name="Foo",
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )
    # Create an inspection system result
    sys_result = InspectResult.objects.create(
        name="Foo",
        status=InspectResult.SUCCESS,
        inspect_group=InspectGroupFactory(),
    )
    sys_result.inspect_group.tasks.add(scan_task)

    RawFact.objects.create(
        name="fact_key", value="fact_value", inspect_result=sys_result
    )

    scanjob.save()

    job_count = len(scan.jobs.all())
    assert job_count != 0
    url = reverse("v1:scan-detail", args=(scan_id,))
    response = client_logged_in.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    job_count = len(scan.jobs.all())
    assert job_count == 0


def test_successful_create(client_logged_in, mocker):
    """A valid create request should succeed."""
    scan = ScanFactory()
    url = reverse("v1:scan-filtered-jobs", args=(scan.id,))
    # avoid triggering an actual scan
    mocker.patch("api.scan.view.start_scan")
    response = client_logged_in.post(url)
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert "id" in response.json()


def test_list_jobs(client_logged_in):
    """List all ScanJobs under a scan."""
    scan = ScanFactory(most_recent_scanjob__report=None)
    scan_job = scan.most_recent_scanjob
    # create another scanjob to ensure it won't appear in the filtered list
    ScanJobFactory()
    url = reverse("v1:scan-filtered-jobs", args=(scan.id,))
    response = client_logged_in.get(url)
    assert response.ok

    results = [
        {
            "id": scan_job.id,
            "scan": {"id": scan.id, "name": scan.name},
            "scan_type": scan.scan_type,
            "options": {"max_concurrency": 25},
            "status": "created",
            "status_message": messages.SJ_STATUS_MSG_CREATED,
            "start_time": mock.ANY,
            "end_time": mock.ANY,
        }
    ]
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": results,
    }


def test_filtered_list(client_logged_in):
    """List filtered ScanJob objects."""
    scan = ScanFactory(most_recent_scanjob__report=None)
    url = reverse("v1:scan-filtered-jobs", args=(scan.id,))

    response = client_logged_in.get(url, {"status": ScanTask.PENDING})
    assert response.ok

    assert response.json() == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }

    response = client_logged_in.get(url, {"status": ScanTask.CREATED})
    assert response.ok

    results1 = [
        {
            "id": scan.most_recent_scanjob.id,
            "scan": {"id": scan.id, "name": scan.name},
            "scan_type": ScanTask.SCAN_TYPE_INSPECT,
            "options": {"max_concurrency": 25},
            "status": "created",
            "status_message": messages.SJ_STATUS_MSG_CREATED,
            "start_time": mock.ANY,
            "end_time": mock.ANY,
        }
    ]
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": results1,
    }
