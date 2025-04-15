"""Test the inspection-related functionality of ScanJobViewSet v1."""

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api.models import InspectResult, RawFact, ScanTask, SystemConnectionResult
from tests.factories import CredentialFactory, InspectGroupFactory, SourceFactory
from tests.scanner.test_util import create_scan_job, create_scan_job_two_tasks

pytestmark = pytest.mark.django_db  # all user tests require the database


def test_inspection_paging(client_logged_in):
    """Test paging of ScanJob inspection results."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scan_job, scan_task = create_scan_job(source)

    # Create an inspection system result
    inspect_sys_result = InspectResult(
        name="Foo",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(source=source),
    )
    inspect_sys_result.save()
    inspect_sys_result.inspect_group.tasks.add(scan_task)

    fact = RawFact(
        name="fact_key",
        value="fact_value",
        inspect_result=inspect_sys_result,
    )
    fact.save()

    inspect_sys_result2 = InspectResult(
        name="Foo",
        status=SystemConnectionResult.FAILED,
        inspect_group=InspectGroupFactory(source=source),
    )
    inspect_sys_result2.save()
    inspect_sys_result2.inspect_group.tasks.add(scan_task)

    fact2 = RawFact(
        name="fact_key2",
        value="fact_value2",
        inspect_result=inspect_sys_result2,
    )
    fact2.save()

    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    response = client_logged_in.get(url, {"page_size": 1})
    assert response.ok
    next_url = (
        "http://testserver"
        f"{reverse('v1:scanjob-inspection', args=(scan_job.id,))}"
        "?page=2&page_size=1"
    )
    assert response.json() == {
        "count": 2,
        "next": next_url,
        "previous": None,
        "results": [
            {
                "name": "Foo",
                "status": "failed",
                "source": {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                },
            }
        ],
    }


def test_inspection_ordering_by_name(client_logged_in):
    """Tests inspection result ordering by name."""
    credential = CredentialFactory()
    source1 = SourceFactory(credentials=[credential])
    source2 = SourceFactory(credentials=[credential])
    scan_job, scan_tasks = create_scan_job_two_tasks(
        source1, source2, ScanTask.SCAN_TYPE_INSPECT
    )
    task_inspect_source_1, task_inspect_source_2, _ = scan_tasks

    # Create an inspection system result
    inspect_sys_result = InspectResult(
        name="Foo1",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(source=source1),
    )
    inspect_sys_result.save()
    inspect_sys_result.inspect_group.tasks.add(task_inspect_source_1)

    inspect_sys_result2 = InspectResult(
        name="Foo2",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(source=source1),
    )
    inspect_sys_result2.save()
    inspect_sys_result2.inspect_group.tasks.add(task_inspect_source_1)

    inspect_sys_result3 = InspectResult(
        name="Foo3",
        status=SystemConnectionResult.FAILED,
        inspect_group=InspectGroupFactory(source=source2),
    )
    inspect_sys_result3.save()
    inspect_sys_result3.inspect_group.tasks.add(task_inspect_source_2)

    inspect_sys_result4 = InspectResult(
        name="Foo4",
        status=SystemConnectionResult.FAILED,
        inspect_group=InspectGroupFactory(source=source2),
    )
    inspect_sys_result4.save()
    inspect_sys_result4.inspect_group.tasks.add(task_inspect_source_2)

    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    response = client_logged_in.get(url, {"ordering": "-name"})
    assert response.ok
    json_response = response.json()
    expected = {
        "count": 4,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Foo4",
                "status": "failed",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
            },
            {
                "name": "Foo3",
                "status": "failed",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
            },
            {
                "name": "Foo2",
                "status": "success",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
            },
            {
                "name": "Foo1",
                "status": "success",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
            },
        ],
    }
    assert json_response == expected


def test_inspection_filter_by_source_id(client_logged_in):
    """Tests inspection result filter by source_id."""
    credential = CredentialFactory()
    source1 = SourceFactory(credentials=[credential])
    source2 = SourceFactory(credentials=[credential])
    scan_job, scan_tasks = create_scan_job_two_tasks(
        source1, source2, ScanTask.SCAN_TYPE_INSPECT
    )
    task_inspect_source_1, task_inspect_source_2, _ = scan_tasks

    # Create an inspection system result
    inspect_sys_result = InspectResult(
        name="Foo1",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(source=source1),
    )
    inspect_sys_result.save()
    inspect_sys_result.inspect_group.tasks.add(task_inspect_source_1)

    inspect_sys_result2 = InspectResult(
        name="Foo2",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(source=source1),
    )
    inspect_sys_result2.save()
    inspect_sys_result2.inspect_group.tasks.add(task_inspect_source_1)

    inspect_sys_result3 = InspectResult(
        name="Foo3",
        status=SystemConnectionResult.FAILED,
        inspect_group=InspectGroupFactory(source=source2),
    )
    inspect_sys_result3.save()
    inspect_sys_result3.inspect_group.tasks.add(task_inspect_source_2)

    inspect_sys_result4 = InspectResult(
        name="Foo4",
        status=SystemConnectionResult.FAILED,
        inspect_group=InspectGroupFactory(source=source2),
    )
    inspect_sys_result4.save()
    inspect_sys_result4.inspect_group.tasks.add(task_inspect_source_2)

    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    response = client_logged_in.get(url, {"source_id": source2.id})
    assert response.ok
    json_resp = response.json()
    expected = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Foo3",
                "status": "failed",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
            },
            {
                "name": "Foo4",
                "status": "failed",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
            },
        ],
    }
    diff = [x for x in expected["results"] if x not in json_resp["results"]]
    assert diff == []


def test_inspection_two_tasks(client_logged_in):
    """Tests inspection result ordering across tasks."""
    credential = CredentialFactory()
    source1 = SourceFactory(credentials=[credential])
    source2 = SourceFactory(credentials=[credential])
    scan_job, scan_tasks = create_scan_job_two_tasks(
        source1, source2, ScanTask.SCAN_TYPE_INSPECT
    )
    task_inspect_source_1, task_inspect_source_2, _ = scan_tasks

    # Create an inspection system result
    inspect_sys_result = InspectResult(
        name="Foo",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(source=source1),
    )
    inspect_sys_result.save()
    inspect_sys_result.inspect_group.tasks.add(task_inspect_source_1)

    inspect_sys_result2 = InspectResult(
        name="Foo",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(
            source=source1,
        ),
    )
    inspect_sys_result2.save()
    inspect_sys_result2.inspect_group.tasks.add(task_inspect_source_1)

    inspect_sys_result3 = InspectResult(
        name="Foo",
        status=SystemConnectionResult.FAILED,
        inspect_group=InspectGroupFactory(
            source=source2,
        ),
    )
    inspect_sys_result3.save()
    inspect_sys_result3.inspect_group.tasks.add(task_inspect_source_2)

    inspect_sys_result4 = InspectResult(
        name="Foo",
        status=SystemConnectionResult.FAILED,
        inspect_group=InspectGroupFactory(
            source=source2,
        ),
    )
    inspect_sys_result4.save()
    inspect_sys_result4.inspect_group.tasks.add(task_inspect_source_2)

    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    response = client_logged_in.get(url)
    assert response.ok
    json_response = response.json()
    expected = {
        "count": 4,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Foo",
                "status": "failed",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
            },
            {
                "name": "Foo",
                "status": "failed",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
            },
            {
                "name": "Foo",
                "status": "success",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
            },
            {
                "name": "Foo",
                "status": "success",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
            },
        ],
    }
    assert json_response == expected


def test_inspection_results_with_none(client_logged_in):
    """Tests inspection results with none for one task."""
    credential = CredentialFactory()
    source1 = SourceFactory(credentials=[credential])
    source2 = SourceFactory(credentials=[credential])
    scan_job, scan_tasks = create_scan_job_two_tasks(
        source1, source2, ScanTask.SCAN_TYPE_INSPECT
    )

    # Create an inspection system result
    inspect_sys_result = InspectResult(
        name="Foo",
        status=SystemConnectionResult.FAILED,
        inspect_group=InspectGroupFactory(
            source=source1,
        ),
    )
    inspect_sys_result.save()
    inspect_sys_result.inspect_group.tasks.add(scan_tasks[2])

    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    response = client_logged_in.get(url)
    assert response.ok
    json_response = response.json()
    expected = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Foo",
                "status": "failed",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
            }
        ],
    }
    assert json_response == expected


def test_inspection_delete_source(client_logged_in):
    """Get ScanJob inspection results after source has been deleted."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scan_job, scan_task = create_scan_job(source)
    # Create an inspection system result
    inspect_result = InspectResult(
        name="Foo",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(
            source=source,
        ),
    )
    inspect_result.save()
    inspect_result.inspect_group.tasks.add(scan_task)
    source.delete()

    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    response = client_logged_in.get(url)
    assert response.ok
    json_response = response.json()
    expected = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Foo",
                "status": "success",
                "source": "deleted",
            }
        ],
    }
    assert json_response == expected


def test_inspection_not_found(client_logged_in):
    """Get ScanJob connection results with 404."""
    url = reverse("v1:scanjob-detail", args="2") + "inspection/"
    response = client_logged_in.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_inspection_bad_request(client_logged_in):
    """Get ScanJob connection results with 400."""
    url = reverse("v1:scanjob-detail", args="t") + "inspection/"
    response = client_logged_in.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_inspection_bad_ordering_filter(client_logged_in):
    """Test ScanJob inspection results with bad ordering filter."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scan_job, scan_task = create_scan_job(source)

    # Create an inspect system result
    inspect_sys_result = InspectResult(
        name="Foo",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(source=source),
    )
    inspect_sys_result.save()
    inspect_sys_result.inspect_group.tasks.add(scan_task)

    fact = RawFact(
        name="fact_key",
        value="fact_value",
        inspect_result=inspect_sys_result,
    )
    fact.save()

    bad_param = "bad_param"
    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    url += "?ordering=" + bad_param
    response = client_logged_in.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_inspection_bad_status_filter(client_logged_in):
    """Test ScanJob inspection results with bad status filter."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scan_job, scan_task = create_scan_job(source)

    # Create an inspection system result
    inspect_sys_result = InspectResult(
        name="Foo",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(
            source=source,
        ),
    )
    inspect_sys_result.save()
    inspect_sys_result.inspect_group.tasks.add(scan_task)

    fact = RawFact(
        name="fact_key",
        value="fact_value",
        inspect_result=inspect_sys_result,
    )
    fact.save()

    bad_param = "bad_param"
    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    url += "?status=" + bad_param
    response = client_logged_in.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_inspection_bad_source_id_filter(client_logged_in):
    """Test ScanJob inspection results with bad source_id filter."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scan_job, scan_task = create_scan_job(source)

    # Create an inspection system result
    inspect_sys_result = InspectResult(
        name="Foo",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(
            source=source,
        ),
    )
    inspect_sys_result.save()
    inspect_sys_result.inspect_group.tasks.add(scan_task)

    fact = RawFact(
        name="fact_key",
        value="fact_value",
        inspect_result=inspect_sys_result,
    )
    fact.save()

    bad_param = "bad_param"
    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    url += "?source_id=" + bad_param
    response = client_logged_in.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_inspection_filter_status(client_logged_in):
    """Get ScanJob inspection results with a filtered status."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scan_job, scan_task = create_scan_job(source)

    # Create an inspection system result
    inspect_sys_result = InspectResult(
        name="Foo",
        status=SystemConnectionResult.SUCCESS,
        inspect_group=InspectGroupFactory(
            source=source,
        ),
    )
    inspect_sys_result.save()
    inspect_sys_result.inspect_group.tasks.add(scan_task)

    fact = RawFact(
        name="fact_key",
        value="fact_value",
        inspect_result=inspect_sys_result,
    )
    fact.save()

    url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
    response = client_logged_in.get(url, {"status": SystemConnectionResult.FAILED})
    assert response.ok
    json_response = response.json()
    expected = {"count": 0, "next": None, "previous": None, "results": []}
    assert json_response == expected
