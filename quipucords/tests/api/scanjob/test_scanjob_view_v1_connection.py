"""Test the connection-related functionality of ScanJobViewSet v1."""

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api.models import ScanTask, SystemConnectionResult
from tests.factories import CredentialFactory, SourceFactory
from tests.scanner.test_util import create_scan_job, create_scan_job_two_tasks

pytestmark = pytest.mark.django_db  # all user tests require the database


def test_connection(client_logged_in):
    """Get ScanJob connection results."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scanjob, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

    # Create a connection system result
    conn_result = scan_task.connection_result
    SystemConnectionResult.objects.create(
        name="Foo",
        source=source,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )

    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url)
    assert response.ok
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Foo",
                "status": SystemConnectionResult.SUCCESS,
                "credential": {"id": credential.id, "name": credential.name},
                "source": {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                },
            }
        ],
    }


@pytest.mark.parametrize("param", ("ordering", "status", "source_id"))
def test_connection_bad_filters(client_logged_in, param):
    """Test ScanJob connection results with bad filters."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scanjob, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

    # Create a connection system result
    conn_result = scan_task.connection_result
    sys_result = SystemConnectionResult(
        name="Foo",
        source=source,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )
    sys_result.save()
    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url, {param: "bad_param"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_connection_filter_status(client_logged_in):
    """Get ScanJob connection results with a filtered status."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scanjob, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

    # Create a connection system result
    conn_result = scan_task.connection_result
    sys_result = SystemConnectionResult(
        name="Foo",
        source=source,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )
    sys_result.save()

    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url, {"status": SystemConnectionResult.FAILED})
    assert response.ok
    assert response.json() == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }


def test_connection_failed_success(client_logged_in):
    """Get ScanJob connection results for multiple systems."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scanjob, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

    # Create two connection system results one failure & one success
    conn_result = scan_task.connection_result
    sys_result = SystemConnectionResult(
        name="Foo",
        source=source,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )
    sys_result.save()
    sys_result = SystemConnectionResult(
        name="Bar",
        source=source,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result,
    )
    sys_result.save()

    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url)
    assert response.ok
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Bar",
                "status": "failed",
                "credential": {"id": credential.id, "name": credential.name},
                "source": {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                },
            },
            {
                "name": "Foo",
                "status": "success",
                "credential": {"id": credential.id, "name": credential.name},
                "source": {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                },
            },
        ],
    }


def test_connection_name_ordering(client_logged_in):
    """Get ScanJob connection results for systems ordered by name."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scanjob, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

    # Create two connection system results one failure & one success
    conn_result = scan_task.connection_result
    sys_result = SystemConnectionResult(
        name="Foo",
        source=source,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )
    sys_result.save()
    sys_result = SystemConnectionResult(
        name="Bar",
        source=source,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result,
    )
    sys_result.save()

    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url, {"ordering": "-name"})
    assert response.ok
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Foo",
                "status": "success",
                "credential": {"id": credential.id, "name": credential.name},
                "source": {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                },
            },
            {
                "name": "Bar",
                "status": "failed",
                "credential": {"id": credential.id, "name": credential.name},
                "source": {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                },
            },
        ],
    }


def test_connection_two_scan_tasks(client_logged_in):
    """Get ScanJob connection results for multiple tasks."""
    # create a second source:
    credential = CredentialFactory()
    source1 = SourceFactory(credentials=[credential])
    source2 = SourceFactory(credentials=[credential])
    scanjob, scan_tasks = create_scan_job_two_tasks(
        source1, source2, ScanTask.SCAN_TYPE_INSPECT
    )

    # Create two connection system results one failure & one success
    conn_result = scan_tasks[0].connection_result
    conn_result2 = scan_tasks[1].connection_result

    sys_result = SystemConnectionResult(
        name="Foo",
        source=source1,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )
    sys_result.save()
    sys_result = SystemConnectionResult(
        name="Bar",
        source=source1,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result,
    )
    sys_result.save()
    sys_result = SystemConnectionResult(
        name="Woot",
        source=source2,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result2,
    )
    sys_result.save()
    sys_result = SystemConnectionResult(
        name="Ness",
        source=source2,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result2,
    )
    sys_result.save()

    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url)
    assert response.ok
    assert response.json() == {
        "count": 4,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Bar",
                "status": "failed",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
            {
                "name": "Woot",
                "status": "failed",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
            {
                "name": "Foo",
                "status": "success",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
            {
                "name": "Ness",
                "status": "success",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
        ],
    }


def test_connection_filter_by_source_id(client_logged_in):
    """Get ScanJob connection results filter by source_id."""
    # create a second source:
    credential = CredentialFactory()
    source1 = SourceFactory(credentials=[credential])
    source2 = SourceFactory(credentials=[credential])
    scanjob, scan_tasks = create_scan_job_two_tasks(
        source1, source2, ScanTask.SCAN_TYPE_INSPECT
    )

    # Create two connection system results one failure & one success
    conn_result = scan_tasks[0].connection_result
    conn_result2 = scan_tasks[1].connection_result
    sys_result = SystemConnectionResult(
        name="Foo",
        source=source1,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )
    sys_result2 = SystemConnectionResult(
        name="Bar",
        source=source1,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result,
    )
    sys_result3 = SystemConnectionResult(
        name="Woot",
        source=source2,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result2,
    )
    sys_result4 = SystemConnectionResult(
        name="Ness",
        source=source2,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result2,
    )
    sys_result.save()
    sys_result2.save()
    sys_result3.save()
    sys_result4.save()

    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url, {"source_id": source2.id})
    assert response.ok
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Woot",
                "status": "failed",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
            {
                "name": "Ness",
                "status": "success",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
        ],
    }


def test_connection_paging(client_logged_in):
    """Test paging for scanjob connection results."""
    # create a second source:
    credential = CredentialFactory()
    source1 = SourceFactory(credentials=[credential])
    source2 = SourceFactory(credentials=[credential])
    scanjob, scan_tasks = create_scan_job_two_tasks(
        source1, source2, ScanTask.SCAN_TYPE_INSPECT
    )

    # Create two connection system results one failure & one success
    conn_result = scan_tasks[0].connection_result
    sys_result = SystemConnectionResult(
        name="Foo",
        source=source1,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )
    sys_result2 = SystemConnectionResult(
        name="Bar",
        source=source1,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result,
    )
    conn_result2 = scan_tasks[1].connection_result
    sys_result3 = SystemConnectionResult(
        name="Woot",
        source=source2,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result2,
    )
    sys_result4 = SystemConnectionResult(
        name="Ness",
        source=source2,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result2,
    )
    sys_result.save()
    sys_result2.save()
    sys_result3.save()
    sys_result4.save()

    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url, {"page_size": 2})
    assert response.ok
    next_url = (
        "http://testserver"
        f"{reverse('v1:scanjob-connection', args=(scanjob.id,))}"
        "?page=2&page_size=2"
    )
    assert response.json() == {
        "count": 4,
        "next": next_url,
        "previous": None,
        "results": [
            {
                "name": "Bar",
                "status": "failed",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
            {
                "name": "Woot",
                "status": "failed",
                "source": {
                    "id": source2.id,
                    "name": source2.name,
                    "source_type": source2.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
        ],
    }


def test_connection_results_with_none(client_logged_in):
    """Test connection results with no results for one task."""
    # create a second source:
    credential = CredentialFactory()
    source1 = SourceFactory(credentials=[credential])
    source2 = SourceFactory(credentials=[credential])
    scanjob, scan_tasks = create_scan_job_two_tasks(
        source1, source2, ScanTask.SCAN_TYPE_INSPECT
    )

    # Create two connection system results one failure & one success
    conn_result = scan_tasks[0].connection_result
    sys_result = SystemConnectionResult(
        name="Foo",
        source=source1,
        credential=credential,
        status=SystemConnectionResult.SUCCESS,
        task_connection_result=conn_result,
    )
    sys_result2 = SystemConnectionResult(
        name="Bar",
        source=source1,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result,
    )
    sys_result.save()
    sys_result2.save()

    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url)
    assert response.ok
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "name": "Bar",
                "status": "failed",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
            {
                "name": "Foo",
                "status": "success",
                "source": {
                    "id": source1.id,
                    "name": source1.name,
                    "source_type": source1.source_type,
                },
                "credential": {"id": credential.id, "name": credential.name},
            },
        ],
    }


def test_connection_delete_source_and_cred(client_logged_in):
    """Get ScanJob connection results after source & cred are deleted."""
    credential = CredentialFactory()
    source = SourceFactory(credentials=[credential])
    scanjob, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

    # Create a connection system result
    conn_result = scan_task.connection_result
    sys_result = SystemConnectionResult(
        name="Woot",
        source=source,
        credential=credential,
        status=SystemConnectionResult.FAILED,
        task_connection_result=conn_result,
    )
    sys_result.save()
    source.delete()
    credential.delete()

    url = reverse("v1:scanjob-connection", args=(scanjob.id,))
    response = client_logged_in.get(url)
    assert response.ok
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"name": "Woot", "status": "failed", "source": "deleted"}],
    }


def test_connection_not_found(client_logged_in):
    """Get ScanJob connection results with 404."""
    url = reverse("v1:scanjob-connection", args=("2",))
    response = client_logged_in.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_connection_bad_request(client_logged_in):
    """Get ScanJob connection results with 400."""
    # TODO IMO this should result in a 404, not 400 - change this behavior in v2
    url = reverse("v1:scanjob-connection", args=("t",))
    response = client_logged_in.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
