"""Test ScanJobViewSet v2 and related v2 view functions."""

import pytest
from rest_framework.reverse import reverse

from api.models import ScanJob, ScanTask
from tests.factories import ScanFactory, ScanJobFactory, ScanTaskFactory, SourceFactory

pytestmark = pytest.mark.django_db  # all tests here require the database


@pytest.fixture
def scan_jobs_and_dicts() -> tuple[list[ScanJob], list[dict]]:
    """Return two inspect-type ScanJobs and their dict representations."""
    scan_jobs = []
    inspect_scan_tasks = []

    source = SourceFactory()
    scan = ScanFactory(sources=[source], most_recent_scanjob=None)

    scan_jobs.append(ScanJobFactory(scan=scan))
    scan_jobs[0].sources.set([source])
    inspect_scan_tasks.append(
        ScanTaskFactory(
            job=scan_jobs[0],
            systems_count=6,
            systems_failed=1,
            systems_scanned=3,
            systems_unreachable=2,
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
        )
    )
    ScanTaskFactory(
        job=scan_jobs[0],
        scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
    )

    scan_jobs.append(ScanJobFactory(scan=scan))
    scan_jobs[1].sources.set([source])
    inspect_scan_tasks.append(
        ScanTaskFactory(
            job=scan_jobs[1],
            systems_count=10,
            systems_failed=2,
            systems_scanned=5,
            systems_unreachable=3,
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
        )
    )
    ScanTaskFactory(
        job=scan_jobs[1],
        scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
    )

    scan.most_recent_scanjob = scan_jobs[1]
    scan.save()

    scan_job_dicts = [
        {
            "id": scan_job.id,
            "end_time": scan_job.end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "report_id": scan_job.report_id,
            "scan_id": scan_job.scan.id,
            "scan_type": scan_job.scan_type,
            "sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                }
            ],
            "start_time": scan_job.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "status": scan_job.status,
            "status_message": scan_job.status_message,
            "systems_count": inspect_scan_tasks[index].systems_count,
            "systems_failed": inspect_scan_tasks[index].systems_failed,
            "systems_scanned": inspect_scan_tasks[index].systems_scanned,
            "systems_unreachable": inspect_scan_tasks[index].systems_unreachable,
        }
        for index, scan_job in enumerate(scan_jobs)
    ]
    return scan_jobs, scan_job_dicts


def test_retrieve(client_logged_in, scan_jobs_and_dicts):
    """Test retrieving a single ScanJob."""
    scan_jobs, scan_jobs_dicts = scan_jobs_and_dicts
    scan_job = scan_jobs[1]
    scan_jobs_dict = scan_jobs_dicts[1]
    url = reverse("v2:job-detail", args=(scan_job.id,))
    response = client_logged_in.get(url)
    assert response.ok
    assert response.json() == scan_jobs_dict


def test_list(client_logged_in, scan_jobs_and_dicts):
    """Test endpoint for listing scan jobs."""
    scan_jobs, scan_jobs_dicts = scan_jobs_and_dicts
    url = reverse("v2:job-list")
    response = client_logged_in.get(url)
    assert response.ok
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": scan_jobs_dicts[::-1],  # default order is -id
    }


def test_max_number_of_queries(client_logged_in, django_assert_max_num_queries):
    """Ensure ScanJobView don't explode in a ridiculous number of queries."""
    ScanJobFactory.create_batch(100)
    url = reverse("v2:job-list")
    # make sure all annotations and prefetches are working so this view don't have
    # N+1 issues
    with django_assert_max_num_queries(5):
        response = client_logged_in.get(url)
    assert response.ok


def test_filter_by_scan_id(client_logged_in, mocker):
    """Test filtering scan job list view by scan id."""
    scan = ScanFactory()
    scan_job = scan.most_recent_scanjob
    # fingerprint type "scans" don't have an actual scan
    scan_job_scanless = ScanJobFactory(scan=None)
    assert scan_job.scan_id
    assert scan_job_scanless.scan_id is None

    url = reverse("v2:job-list")
    response = client_logged_in.get(url)
    assert response.ok
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [mocker.ANY, mocker.ANY],
    }
    # this is also testing default ordering (-id)
    assert [result["id"] for result in response.json()["results"]] == [
        scan_job_scanless.id,
        scan_job.id,
    ]
    # filter by scan_id
    response2 = client_logged_in.get(url, {"scan_id": scan_job.scan_id})
    assert response2.ok
    assert response2.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [mocker.ANY],
    }
    assert response2.json()["results"][0]["id"] == scan_job.id
    assert response2.json()["results"][0]["scan_id"] == scan_job.scan_id
    # filter scanless jobs
    response3 = client_logged_in.get(url, {"scan_id__isnull": True})
    assert response3.ok
    assert response3.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [mocker.ANY],
    }
    assert response3.json()["results"][0]["id"] == scan_job_scanless.id
    assert response3.json()["results"][0]["scan_id"] is None


def test_filter_by_scan_type(client_logged_in, mocker, faker):
    """Test filtering scan job list by scan_type."""
    for scan_type, _ in ScanTask.SCANTASK_TYPE_CHOICES:
        ScanJobFactory(scan_type=scan_type)
    chosen_type, _ = faker.random_element(ScanTask.SCANTASK_TYPE_CHOICES)
    scan_job = ScanJob.objects.get(scan_type=chosen_type)
    url = reverse("v2:job-list")
    response = client_logged_in.get(url, {"scan_type": chosen_type})
    assert response.ok
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [mocker.ANY],
    }
    result = response.json()["results"][0]
    assert result["id"] == scan_job.id
    assert result["scan_type"] == chosen_type


def test_filter_by_status(client_logged_in, mocker, faker):
    """Test filtering scan job list by status."""
    for scan_job_status, _ in ScanTask.STATUS_CHOICES:
        ScanJobFactory(status=scan_job_status)
    chosen_status, _ = faker.random_element(ScanTask.STATUS_CHOICES)
    scan_job = ScanJob.objects.get(status=chosen_status)
    url = reverse("v2:job-list")
    response = client_logged_in.get(url, {"status": chosen_status})
    assert response.ok
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [mocker.ANY],
    }
    result = response.json()["results"][0]
    assert result["id"] == scan_job.id
    assert result["status"] == chosen_status
