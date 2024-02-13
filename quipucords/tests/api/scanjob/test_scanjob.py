"""Test the API application."""


from unittest import mock

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from api import messages
from api.models import (
    DisabledOptionalProductsOptions,
    ExtendedProductSearchOptions,
    RawFact,
    ScanJob,
    ScanOptions,
    ScanTask,
    SystemConnectionResult,
    SystemInspectionResult,
)
from api.scan.serializer import ExtendedProductSearchOptionsSerializer
from api.scanjob.serializer import ScanJobSerializer
from api.scanjob.view import expand_scanjob
from tests.factories import (
    CredentialFactory,
    ScanFactory,
    ScanJobFactory,
    ScanOptionsFactory,
    SourceFactory,
)
from tests.scanner.test_util import (
    create_scan_job,
    create_scan_job_two_tasks,
    scan_options_products,
)


@pytest.mark.django_db
class TestScanJob:
    """Test the basic ScanJob infrastructure."""

    def test_queue_task(self, django_client):
        """Test create queue state change."""
        scan_options = ScanOptionsFactory()
        scan = ScanFactory(options=scan_options)
        # Create Job
        scan_job = ScanJob.objects.create(scan=scan)

        # Job in created state
        assert scan_job.status == ScanTask.CREATED
        tasks = scan_job.tasks.all()
        assert len(tasks) == 0

        # Queue job to run
        scan_job.queue()

        # Job should be in pending state
        assert scan_job.status == ScanTask.PENDING

        # Queue should have created scan tasks
        tasks = scan_job.tasks.all().order_by("sequence_number")
        assert len(tasks) == 3

        # Validate connect task created and correct
        connect_task = tasks[0]
        assert connect_task.scan_type == ScanTask.SCAN_TYPE_CONNECT
        assert connect_task.status == ScanTask.PENDING

        # Validate inspect task created and correct
        inspect_task = tasks[1]
        assert inspect_task.scan_type == ScanTask.SCAN_TYPE_INSPECT
        assert inspect_task.status == ScanTask.PENDING

    def test_queue_invalid_state_changes(self, django_client):
        """Test create queue failed."""
        scan_job, _ = create_scan_job(
            SourceFactory(), scan_type=ScanTask.SCAN_TYPE_INSPECT
        )
        scan_job.status = ScanTask.FAILED

        # Queue job to run
        scan_job.queue()
        assert scan_job.status == ScanTask.FAILED

        assert not scan_job.status_complete()
        assert scan_job.status == ScanTask.FAILED

        assert not scan_job.status_pause()
        assert scan_job.status == ScanTask.FAILED

        assert not scan_job.status_start()
        assert scan_job.status == ScanTask.FAILED

        assert not scan_job.status_cancel()
        assert scan_job.status == ScanTask.FAILED

        assert not scan_job.status_restart()
        assert scan_job.status == ScanTask.FAILED

        assert scan_job.status_fail("test failure")
        assert scan_job.status == ScanTask.FAILED

        scan_job.status = ScanTask.CREATED
        assert not scan_job.status_fail("test failure")
        assert scan_job.status == ScanTask.CREATED

        scan_job.status = ScanTask.RUNNING
        assert scan_job.status_complete()
        assert scan_job.status == ScanTask.COMPLETED

    def test_start_task(self, django_client):
        """Test start pending task."""
        scan_job, _ = create_scan_job(
            SourceFactory(), scan_type=ScanTask.SCAN_TYPE_CONNECT
        )

        # Queue job to run
        scan_job.queue()
        assert scan_job.status == ScanTask.PENDING

        # Queue should have created scan tasks
        tasks = scan_job.tasks.all()
        assert len(tasks) == 1

        # Start job
        assert scan_job.status_start()

    def test_pause_restart_task(self, django_client):
        """Test pause and restart task."""
        scan_job, _ = create_scan_job(
            SourceFactory(), scan_type=ScanTask.SCAN_TYPE_CONNECT
        )

        # Queue job to run
        scan_job.queue()
        assert scan_job.status == ScanTask.PENDING

        # Queue should have created scan tasks
        tasks = scan_job.tasks.all()
        assert len(tasks) == 1
        connect_task = scan_job.tasks.first()
        assert connect_task.status == ScanTask.PENDING

        # Start job
        assert scan_job.status_start()
        assert scan_job.status == ScanTask.RUNNING

        assert scan_job.status_pause()
        connect_task = scan_job.tasks.first()
        assert scan_job.status == ScanTask.PAUSED
        assert connect_task.status == ScanTask.PAUSED

        assert scan_job.status_restart()
        connect_task = scan_job.tasks.first()
        assert scan_job.status == ScanTask.PENDING
        assert connect_task.status == ScanTask.PENDING

        assert scan_job.status_cancel()
        connect_task = scan_job.tasks.first()
        assert scan_job.status == ScanTask.CANCELED
        assert connect_task.status == ScanTask.CANCELED

    def test_successful_create(self, django_client, mocker):
        """A valid create request should succeed."""
        scan = ScanFactory()
        url = reverse("v1:scan-filtered-jobs", args=(scan.id,))
        # avoid triggering an actual scan
        mocker.patch("api.scan.view.start_scan")
        response = django_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED, response.json()
        assert "id" in response.json()

    def test_retrieve(self, django_client):
        """Get ScanJob details by primary key."""
        scan = ScanFactory()
        scanjob = scan.most_recent_scanjob
        url = reverse("v1:scanjob-detail", args=(scanjob.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "scan" in response.json()
        scan_json = response.json()["scan"]
        assert scan_json == {"id": scan.id, "name": scan.name}

    def test_connection(self, django_client):
        """Get ScanJob connection results."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=source,
            credential=credential,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()

        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
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
    def test_connection_bad_filters(self, django_client, param):
        """Test ScanJob connection results with bad filters."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=source,
            credential=credential,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()
        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(url, params={param: "bad_param"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_connection_filter_status(self, django_client):
        """Get ScanJob connection results with a filtered status."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=source,
            credential=credential,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()

        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(
            url, params={"status": SystemConnectionResult.FAILED}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "count": 0,
            "next": None,
            "previous": None,
            "results": [],
        }

    def test_connection_failed_success(self, django_client):
        """Get ScanJob connection results for multiple systems."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create two connection system results one failure & one success
        conn_result = scan_task.prerequisites.first().connection_result
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

        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
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

    def test_connection_name_ordering(self, django_client):
        """Get ScanJob connection results for systems ordered by name."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create two connection system results one failure & one success
        conn_result = scan_task.prerequisites.first().connection_result
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

        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(url, params={"ordering": "-name"})
        assert response.status_code == status.HTTP_200_OK
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

    def test_connection_two_scan_tasks(self, django_client):
        """Get ScanJob connection results for multiple tasks."""
        # create a second source:
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_CONNECT
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

        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
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

    def test_connection_filter_by_source_id(self, django_client):
        """Get ScanJob connection results filter by source_id."""
        # create a second source:
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_CONNECT
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

        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(url, params={"source_id": source2.id})
        assert response.status_code == status.HTTP_200_OK
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

    def test_connection_paging(self, django_client, live_server):
        """Test paging for scanjob connection results."""
        # create a second source:
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_CONNECT
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

        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(url, params={"page_size": 2})
        assert response.status_code == status.HTTP_200_OK
        next_url = (
            f"{live_server.url}"
            f"{reverse('v1:scanjob-connection', args=(scan_job.id,))}"
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

    def test_connection_results_with_none(self, django_client):
        """Test connection results with no results for one task."""
        # create a second source:
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_CONNECT
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

        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
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

    def test_connection_delete_source_and_cred(self, django_client):
        """Get ScanJob connection results after source & cred are deleted."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_CONNECT)

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

        url = reverse("v1:scanjob-connection", args=(scan_job.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [{"name": "Woot", "status": "failed", "source": "deleted"}],
        }

    def test_connection_not_found(self, django_client):
        """Get ScanJob connection results with 404."""
        url = reverse("v1:scanjob-detail", args="2") + "connection/"
        response = django_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_connection_bad_request(self, django_client):
        """Get ScanJob connection results with 400."""
        # TODO IMO this should result in a 404, not 400 - change this behavior in v2
        url = reverse("v1:scanjob-detail", args="t") + "connection/"
        response = django_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inspection_bad_ordering_filter(self, django_client):
        """Test ScanJob inspection results with bad ordering filter."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        bad_param = "bad_param"
        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        url += "?ordering=" + bad_param
        response = django_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inspection_bad_status_filter(self, django_client):
        """Test ScanJob inspection results with bad status filter."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        bad_param = "bad_param"
        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        url += "?status=" + bad_param
        response = django_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inspection_bad_source_id_filter(self, django_client):
        """Test ScanJob inspection results with bad source_id filter."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        bad_param = "bad_param"
        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        url += "?source_id=" + bad_param
        response = django_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inspection_filter_status(self, django_client):
        """Get ScanJob inspection results with a filtered status."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        url += "?status=" + SystemConnectionResult.FAILED
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        expected = {"count": 0, "next": None, "previous": None, "results": []}
        assert json_response == expected

    def test_inspection_paging(self, django_client, live_server):
        """Test paging of ScanJob inspection results."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        inspect_sys_result2 = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.FAILED,
            source=source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result2.save()

        fact2 = RawFact(
            name="fact_key2",
            value="fact_value2",
            system_inspection_result=inspect_sys_result2,
        )
        fact2.save()

        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        response = django_client.get(url, params={"page_size": 1})
        assert response.status_code == status.HTTP_200_OK
        next_url = (
            f"{live_server.url}"
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
                    "facts": [{"name": "fact_key2", "value": "fact_value2"}],
                }
            ],
        }

    def test_inspection_ordering_by_name(self, django_client):
        """Tests inspection result ordering by name."""
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        inspection_result = scan_tasks[2].inspection_result
        inspection_result2 = scan_tasks[3].inspection_result
        # Create an inspection system result
        inspect_sys_result = SystemInspectionResult(
            name="Foo1",
            status=SystemConnectionResult.SUCCESS,
            source=source1,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        inspect_sys_result2 = SystemInspectionResult(
            name="Foo2",
            status=SystemConnectionResult.SUCCESS,
            source=source1,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result2.save()

        fact2 = RawFact(
            name="fact_key2",
            value="fact_value2",
            system_inspection_result=inspect_sys_result2,
        )
        fact2.save()

        inspect_sys_result3 = SystemInspectionResult(
            name="Foo3",
            status=SystemConnectionResult.FAILED,
            source=source2,
            task_inspection_result=inspection_result2,
        )
        inspect_sys_result3.save()

        inspect_sys_result4 = SystemInspectionResult(
            name="Foo4",
            status=SystemConnectionResult.FAILED,
            source=source2,
            task_inspection_result=inspection_result2,
        )
        inspect_sys_result4.save()

        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        response = django_client.get(url, params={"ordering": "-name"})
        assert response.status_code == status.HTTP_200_OK
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
                    "facts": [],
                },
                {
                    "name": "Foo3",
                    "status": "failed",
                    "source": {
                        "id": source2.id,
                        "name": source2.name,
                        "source_type": source2.source_type,
                    },
                    "facts": [],
                },
                {
                    "name": "Foo2",
                    "status": "success",
                    "source": {
                        "id": source1.id,
                        "name": source1.name,
                        "source_type": source1.source_type,
                    },
                    "facts": [{"name": "fact_key2", "value": "fact_value2"}],
                },
                {
                    "name": "Foo1",
                    "status": "success",
                    "source": {
                        "id": source1.id,
                        "name": source1.name,
                        "source_type": source1.source_type,
                    },
                    "facts": [{"name": "fact_key", "value": "fact_value"}],
                },
            ],
        }
        assert json_response == expected

    def test_inspection_filter_by_source_id(self, django_client):
        """Tests inspection result filter by source_id."""
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        # Create an inspection system result
        inspection_result = scan_tasks[2].inspection_result
        inspection_result2 = scan_tasks[3].inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo1",
            status=SystemConnectionResult.SUCCESS,
            source=source1,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        inspect_sys_result2 = SystemInspectionResult(
            name="Foo2",
            status=SystemConnectionResult.SUCCESS,
            source=source1,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result2.save()

        fact2 = RawFact(
            name="fact_key2",
            value="fact_value2",
            system_inspection_result=inspect_sys_result2,
        )
        fact2.save()

        inspect_sys_result3 = SystemInspectionResult(
            name="Foo3",
            status=SystemConnectionResult.FAILED,
            source=source2,
            task_inspection_result=inspection_result2,
        )
        inspect_sys_result3.save()

        inspect_sys_result4 = SystemInspectionResult(
            name="Foo4",
            status=SystemConnectionResult.FAILED,
            source=source2,
            task_inspection_result=inspection_result2,
        )
        inspect_sys_result4.save()

        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        response = django_client.get(url, params={"source_id": source2.id})
        assert response.status_code == status.HTTP_200_OK
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
                    "facts": [],
                },
                {
                    "name": "Foo4",
                    "status": "failed",
                    "source": {
                        "id": source2.id,
                        "name": source2.name,
                        "source_type": source2.source_type,
                    },
                    "facts": [],
                },
            ],
        }
        diff = [x for x in expected["results"] if x not in json_resp["results"]]
        assert diff == []

    def test_inspection_two_tasks(self, django_client):
        """Tests inspection result ordering across tasks."""
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        # Create an inspection system result
        inspection_result = scan_tasks[2].inspection_result
        inspection_result2 = scan_tasks[3].inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=source1,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        inspect_sys_result2 = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=source1,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result2.save()

        fact2 = RawFact(
            name="fact_key2",
            value="fact_value2",
            system_inspection_result=inspect_sys_result2,
        )
        fact2.save()

        inspect_sys_result3 = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.FAILED,
            source=source2,
            task_inspection_result=inspection_result2,
        )
        inspect_sys_result3.save()

        inspect_sys_result4 = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.FAILED,
            source=source2,
            task_inspection_result=inspection_result2,
        )
        inspect_sys_result4.save()

        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
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
                    "facts": [],
                },
                {
                    "name": "Foo",
                    "status": "failed",
                    "source": {
                        "id": source2.id,
                        "name": source2.name,
                        "source_type": source2.source_type,
                    },
                    "facts": [],
                },
                {
                    "name": "Foo",
                    "status": "success",
                    "source": {
                        "id": source1.id,
                        "name": source1.name,
                        "source_type": source1.source_type,
                    },
                    "facts": [{"name": "fact_key", "value": "fact_value"}],
                },
                {
                    "name": "Foo",
                    "status": "success",
                    "source": {
                        "id": source1.id,
                        "name": source1.name,
                        "source_type": source1.source_type,
                    },
                    "facts": [{"name": "fact_key2", "value": "fact_value2"}],
                },
            ],
        }
        assert json_response == expected

    def test_inspection_results_with_none(self, django_client):
        """Tests inspection results with none for one task."""
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        # Create an inspection system result
        inspection_result = scan_tasks[2].inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.FAILED,
            source=source1,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
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
                    "facts": [{"name": "fact_key", "value": "fact_value"}],
                }
            ],
        }
        assert json_response == expected

    def test_inspection_delete_source(self, django_client):
        """Get ScanJob inspection results after source has been deleted."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        source.delete()

        url = reverse("v1:scanjob-inspection", args=(scan_job.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK
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
                    "facts": [{"name": "fact_key", "value": "fact_value"}],
                }
            ],
        }
        assert json_response == expected

    def test_inspection_not_found(self, django_client):
        """Get ScanJob connection results with 404."""
        url = reverse("v1:scanjob-detail", args="2") + "inspection/"
        response = django_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_inspection_bad_request(self, django_client):
        """Get ScanJob connection results with 400."""
        url = reverse("v1:scanjob-detail", args="t") + "inspection/"
        response = django_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_jobs_not_allowed(self, django_client):
        """Test post jobs not allowed."""
        url = reverse("v1:scanjob-detail", args=(1,))
        url = url[:-2]
        response = django_client.post(url, {})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_not_allowed(self, django_client):
        """Test list all jobs not allowed."""
        url = reverse("v1:scanjob-detail", args=(1,))
        url = url[:-2]
        response = django_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_not_allowed(self, django_client):
        """Test update scanjob not allowed."""
        source = SourceFactory()
        scan = ScanFactory()

        data = {
            "sources": [source.id],
            "scan_type": ScanTask.SCAN_TYPE_INSPECT,
            "options": {
                "disabled_optional_products": {
                    "jboss_eap": True,
                    "jboss_fuse": True,
                    "jboss_brms": True,
                    "jboss_ws": True,
                }
            },
        }
        url = reverse("v1:scanjob-detail", args=(scan.most_recent_scanjob.id,))
        response = django_client.put(url, json=data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_not_allowed_disable_optional_products(self, django_client):
        """Test update scan job options not allowed."""
        scan = ScanFactory()
        scan_job = scan.most_recent_scanjob
        source = SourceFactory()

        data = {
            "sources": [source.id],
            "scan_type": ScanTask.SCAN_TYPE_INSPECT,
            "options": {"disabled_optional_products": "bar"},
        }
        url = reverse("v1:scanjob-detail", args=(scan_job.id,))
        response = django_client.put(url, json=data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_partial_update(self, django_client):
        """Test partial update not allow for scanjob."""
        scan = ScanFactory()
        scan_job = scan.most_recent_scanjob

        data = {"scan_type": ScanTask.SCAN_TYPE_INSPECT}
        url = reverse("v1:scanjob-detail", args=(scan_job.id,))
        response = django_client.patch(url, json=data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete(self, django_client):
        """Delete a ScanJob is not supported."""
        scan_job = ScanJobFactory()

        url = reverse("v1:scanjob-detail", args=(scan_job.id,))
        response = django_client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_pause_bad_state(self, django_client):
        """Pause a scanjob."""
        scan_job = ScanJobFactory()

        url = reverse("v1:scanjob-pause", args=(scan_job.id,))
        response = django_client.put(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pause_bad_id(self, django_client):
        """Pause a scanjob with bad id."""
        url = reverse("v1:scanjob-pause", args=("string",))
        response = django_client.put(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancel(self, django_client):
        """Cancel a scanjob."""
        scan_job = ScanJobFactory()
        url = reverse("v1:scanjob-cancel", args=(scan_job.id,))
        response = django_client.put(url)
        assert response.status_code == status.HTTP_200_OK

    def test_cancel_bad_id(self, django_client):
        """Cancel a scanjob with bad id."""
        url = reverse("v1:scanjob-cancel", args=("string",))
        response = django_client.put(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_restart_bad_state(self, django_client):
        """Restart a scanjob."""
        scan_job = ScanJobFactory()

        url = reverse("v1:scanjob-restart", args=(scan_job.id,))
        response = django_client.put(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_restart_bad_id(self, django_client):
        """Restart a scanjob with bad id."""
        url = reverse("v1:scanjob-restart", args=("string",))
        response = django_client.put(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_expand_scanjob(self):
        """Test view expand_scanjob."""
        scan_job, scan_task = create_scan_job(
            SourceFactory(), scan_type=ScanTask.SCAN_TYPE_INSPECT
        )
        connect_task = scan_task.prerequisites.first()
        scan_job.status = ScanTask.RUNNING
        scan_job.save()
        connect_task.update_stats(
            "TEST_VC", sys_count=2, sys_failed=0, sys_scanned=2, sys_unreachable=0
        )
        scan_task.update_stats(
            "TEST_VC.", sys_count=2, sys_failed=1, sys_scanned=1, sys_unreachable=0
        )

        scan_job = ScanJob.objects.filter(pk=scan_job.id).first()
        serializer = ScanJobSerializer(scan_job)
        json_scan = serializer.data
        json_scan = expand_scanjob(json_scan)

        assert json_scan.get("systems_count") == 2
        assert json_scan.get("systems_failed") == 1
        assert json_scan.get("systems_scanned") == 1

    def test_expand_scanjob_calc(self):
        """Test view expand_scanjob calculations."""
        scan_job, scan_tasks = create_scan_job_two_tasks(
            SourceFactory(), SourceFactory(), scan_type=ScanTask.SCAN_TYPE_INSPECT
        )
        scan_job.status = ScanTask.RUNNING
        scan_job.save()
        counts = (
            (15, 10, 2, 3),  # connect source 1
            (40, 39, 0, 1),  # connect source 2
            (10, 9, 1, 0),  # inspect source 1
            (39, 30, 2, 7),  # inspect source 2
        )
        for task, count_spec in zip(scan_tasks, counts):
            count, scanned, failed, unreachable = count_spec
            task.update_stats(
                f"test-{count}",
                sys_count=count,
                sys_scanned=scanned,
                sys_failed=failed,
                sys_unreachable=unreachable,
            )

        scan_job = ScanJob.objects.filter(pk=scan_job.id).first()
        serializer = ScanJobSerializer(scan_job)
        json_scan = serializer.data
        json_scan = expand_scanjob(json_scan)

        assert json_scan.get("systems_count") == 55
        assert json_scan.get("systems_scanned") == 39
        assert json_scan.get("systems_failed") == 5
        assert json_scan.get("systems_unreachable") == 11

        for json_task, count_spec in zip(json_scan.get("tasks"), counts):
            count, scanned, failed, unreachable = count_spec
            assert json_task.get("systems_count") == count
            assert json_task.get("systems_scanned") == scanned
            assert json_task.get("systems_failed") == failed
            assert json_task.get("systems_unreachable") == unreachable

    def test_get_extra_vars(self):
        """Tests the get_extra_vars method with empty dict."""
        extended = ExtendedProductSearchOptions.objects.create()
        disabled = DisabledOptionalProductsOptions.objects.create()
        scan_options = ScanOptions.objects.create(
            disabled_optional_products=disabled,
            enabled_extended_product_search=extended,
        )
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_brms": True,
            "jboss_ws": True,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_brms_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        json_disabled, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializer(scan_job)
        json_scan = serializer.data
        assert (
            json_scan.get("options").get("disabled_optional_products") == json_disabled
        )
        assert (
            json_scan.get("options").get("enabled_extended_product_search")
            == json_enabled_ext
        )

    def test_get_extra_vars_missing_disable_product(self):
        """Tests the get_extra_vars with extended search None."""
        disabled = DisabledOptionalProductsOptions.objects.create()
        scan_options = ScanOptions.objects.create(disabled_optional_products=disabled)
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_brms": True,
            "jboss_ws": True,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_brms_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        json_disabled, _ = scan_options_products(expected_vars)

        serializer = ScanJobSerializer(scan_job)
        json_scan = serializer.data
        assert (
            json_scan.get("options").get("disabled_optional_products") == json_disabled
        )
        assert json_scan.get("options").get("enabled_extended_product_search") is None

    def test_get_extra_vars_missing_extended_search(self):
        """Tests the get_extra_vars with disabled products None."""
        extended = ExtendedProductSearchOptions.objects.create()
        scan_options = ScanOptions.objects.create(
            enabled_extended_product_search=extended
        )
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_brms": True,
            "jboss_ws": True,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_brms_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        _, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializer(scan_job)
        json_scan = serializer.data
        assert json_scan.get("options").get("disabled_optional_products") is None
        assert (
            json_scan.get("options").get("enabled_extended_product_search")
            == json_enabled_ext
        )

    def test_get_extra_vars_missing_search_directories_empty(self):
        """Tests the get_extra_vars with search_directories empty."""
        extended = {"search_directories": []}
        serializer = ExtendedProductSearchOptionsSerializer(data=extended)
        assert serializer.is_valid()

    def test_get_extra_vars_missing_search_directories_w_int(self, django_client):
        """Tests the get_extra_vars with search_directories contains int."""
        extended = {"search_directories": [1]}
        serializer = ExtendedProductSearchOptionsSerializer(data=extended)
        assert not serializer.is_valid()

    def test_get_extra_vars_missing_search_directories_w_not_path(self, django_client):
        """Tests the get_extra_vars with search_directories no path."""
        extended = {"search_directories": ["a"]}
        serializer = ExtendedProductSearchOptionsSerializer(data=extended)
        assert not serializer.is_valid()

    def test_get_extra_vars_missing_search_directories_w_path(self):
        """Tests the get_extra_vars with search_directories no path."""
        extended = {"search_directories": ["/a"]}
        serializer = ExtendedProductSearchOptionsSerializer(data=extended)
        assert serializer.is_valid()

    def test_get_extra_vars_extended_search(self):
        """Tests the get_extra_vars method with extended search."""
        extended = ExtendedProductSearchOptions.objects.create(
            jboss_eap=True,
            jboss_fuse=True,
            jboss_brms=True,
            jboss_ws=True,
            search_directories=["a", "b"],
        )
        disabled = DisabledOptionalProductsOptions.objects.create()
        scan_options = ScanOptions.objects.create(
            disabled_optional_products=disabled,
            enabled_extended_product_search=extended,
        )
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_brms": True,
            "jboss_ws": True,
            "jboss_eap_ext": True,
            "jboss_fuse_ext": True,
            "jboss_brms_ext": True,
            "jboss_ws_ext": True,
            "search_directories": "a b",
        }
        assert extra_vars == expected_vars

        json_disabled, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializer(scan_job)
        json_scan = serializer.data
        assert (
            json_scan.get("options").get("disabled_optional_products") == json_disabled
        )
        assert json_scan.get("options").get(
            "enabled_extended_product_search"
        ) == json_enabled_ext | {"search_directories": ["a", "b"]}

    def test_get_extra_vars_mixed(self):
        """Tests the get_extra_vars method with mixed values."""
        extended = ExtendedProductSearchOptions.objects.create()
        disabled = DisabledOptionalProductsOptions.objects.create(
            jboss_eap=True, jboss_fuse=True, jboss_brms=False, jboss_ws=False
        )
        scan_options = ScanOptions.objects.create(
            disabled_optional_products=disabled,
            enabled_extended_product_search=extended,
        )
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": False,
            "jboss_brms": True,
            "jboss_ws": True,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_brms_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        json_disabled, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializer(scan_job)
        json_scan = serializer.data
        # jboss_eap is calculated based on all the other values - it's easier this way
        assert json_scan.get("options").get(
            "disabled_optional_products"
        ) == json_disabled | {"jboss_eap": True}
        assert (
            json_scan.get("options").get("enabled_extended_product_search")
            == json_enabled_ext
        )

    def test_get_extra_vars_false(self):
        """Tests the get_extra_vars method with all False."""
        extended = ExtendedProductSearchOptions.objects.create()
        disabled = DisabledOptionalProductsOptions.objects.create(
            jboss_eap=True, jboss_fuse=True, jboss_brms=True, jboss_ws=True
        )
        scan_options = ScanOptions.objects.create(
            disabled_optional_products=disabled,
            enabled_extended_product_search=extended,
        )
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )

        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {
            "jboss_eap": False,
            "jboss_fuse": False,
            "jboss_brms": False,
            "jboss_ws": False,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_brms_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        json_disabled, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializer(scan_job)
        json_scan = serializer.data
        assert (
            json_scan.get("options").get("disabled_optional_products") == json_disabled
        )
        assert (
            json_scan.get("options").get("enabled_extended_product_search")
            == json_enabled_ext
        )

    # ############################################################
    # # Scan Job tests /jobs path
    # ############################################################
    def test_list_jobs(self, django_client):
        """List all ScanJobs under a scan."""
        scan = ScanFactory(most_recent_scanjob__report=None)
        scan_job = scan.most_recent_scanjob
        # create another scanjob to ensure it wont appear in the filtered list
        ScanJobFactory()
        url = reverse("v1:scan-filtered-jobs", args=(scan.id,))
        response = django_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        results = [
            {
                "id": scan_job.id,
                "scan": {"id": scan.id, "name": scan.name},
                "scan_type": scan.scan_type,
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

    def test_filtered_list(self, django_client):
        """List filtered ScanJob objects."""
        scan = ScanFactory(most_recent_scanjob__report=None)
        url = reverse("v1:scan-filtered-jobs", args=(scan.id,))

        response = django_client.get(url, params={"status": ScanTask.PENDING})
        assert response.status_code == status.HTTP_200_OK

        assert response.json() == {
            "count": 0,
            "next": None,
            "previous": None,
            "results": [],
        }

        response = django_client.get(url, params={"status": ScanTask.CREATED})
        assert response.status_code == status.HTTP_200_OK

        results1 = [
            {
                "id": scan.most_recent_scanjob.id,
                "scan": {"id": scan.id, "name": scan.name},
                "scan_type": ScanTask.SCAN_TYPE_INSPECT,
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

    def test_delete_scan_cascade(self, django_client):
        """Delete a scan and its related data."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

        scan = scan_job.scan
        scan_id = scan.id

        # self.create_job_expect_201(scan_id)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        SystemConnectionResult.objects.create(
            name="Foo",
            credential=credential,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        # Create an inspection system result
        inspect_result = scan_task.inspection_result
        sys_result = SystemInspectionResult.objects.create(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            task_inspection_result=inspect_result,
        )

        RawFact.objects.create(
            name="fact_key", value="fact_value", system_inspection_result=sys_result
        )

        scan_job.save()

        job_count = len(scan.jobs.all())
        assert job_count != 0
        url = reverse("v1:scan-detail", args=(scan_id,))
        response = django_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        job_count = len(scan.jobs.all())
        assert job_count == 0
