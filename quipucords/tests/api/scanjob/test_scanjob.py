"""Test the API application."""

import random
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

from api import messages
from api.models import (
    InspectGroup,
    InspectResult,
    RawFact,
    Scan,
    ScanJob,
    ScanTask,
    SystemConnectionResult,
)
from api.scan.serializer import ScanSerializer
from api.scanjob.serializer_v1 import ScanJobSerializerV1
from api.scanjob.view_v1 import expand_scanjob
from tests.api.scan.test_scan import (
    disabled_optional_products_default,
    enabled_extended_product_search_default,
)
from tests.factories import (
    CredentialFactory,
    InspectGroupFactory,
    InspectResultFactory,
    ReportFactory,
    ScanFactory,
    ScanJobFactory,
    ScanTaskFactory,
    SourceFactory,
)
from tests.scanner.test_util import (
    create_scan_job,
    create_scan_job_two_tasks,
    scan_options_products,
)

if TYPE_CHECKING:
    from api.models import Report, ScanJob


@pytest.mark.django_db
class TestScanJob:
    """Test the basic ScanJob infrastructure."""

    def test_queue_task(self, client_logged_in):
        """Test create queue state change."""
        scan_options = {
            "disabled_optional_products": disabled_optional_products_default(),
            "enabled_extended_product_search": (
                enabled_extended_product_search_default()
            ),
        }
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

    def test_queue_invalid_state_changes(self, client_logged_in):
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

    def test_start_task(self, client_logged_in):
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

    def test_pause_restart_task(self, client_logged_in):
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

    def test_successful_create(self, client_logged_in, mocker):
        """A valid create request should succeed."""
        scan = ScanFactory()
        url = reverse("v1:scan-filtered-jobs", args=(scan.id,))
        # avoid triggering an actual scan
        mocker.patch("api.scan.view.start_scan")
        response = client_logged_in.post(url)
        assert response.status_code == status.HTTP_201_CREATED, response.json()
        assert "id" in response.json()

    def test_retrieve(self, client_logged_in):
        """Get ScanJob details by primary key."""
        scan = ScanFactory()
        scanjob = scan.most_recent_scanjob
        url = reverse("v1:scanjob-detail", args=(scanjob.id,))
        response = client_logged_in.get(url)
        assert response.ok
        assert "scan" in response.json()
        scan_json = response.json()["scan"]
        assert scan_json == {"id": scan.id, "name": scan.name}

    def test_connection(self, client_logged_in):
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
    def test_connection_bad_filters(self, client_logged_in, param):
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
        response = client_logged_in.get(url, {param: "bad_param"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_connection_filter_status(self, client_logged_in):
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
        response = client_logged_in.get(url, {"status": SystemConnectionResult.FAILED})
        assert response.ok
        assert response.json() == {
            "count": 0,
            "next": None,
            "previous": None,
            "results": [],
        }

    def test_connection_failed_success(self, client_logged_in):
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

    def test_connection_name_ordering(self, client_logged_in):
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

    def test_connection_two_scan_tasks(self, client_logged_in):
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

    def test_connection_filter_by_source_id(self, client_logged_in):
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

    def test_connection_paging(self, client_logged_in):
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
        response = client_logged_in.get(url, {"page_size": 2})
        assert response.ok
        next_url = (
            "http://testserver"
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

    def test_connection_results_with_none(self, client_logged_in):
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

    def test_connection_delete_source_and_cred(self, client_logged_in):
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
        response = client_logged_in.get(url)
        assert response.ok
        assert response.json() == {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [{"name": "Woot", "status": "failed", "source": "deleted"}],
        }

    def test_connection_not_found(self, client_logged_in):
        """Get ScanJob connection results with 404."""
        url = reverse("v1:scanjob-detail", args="2") + "connection/"
        response = client_logged_in.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_connection_bad_request(self, client_logged_in):
        """Get ScanJob connection results with 400."""
        # TODO IMO this should result in a 404, not 400 - change this behavior in v2
        url = reverse("v1:scanjob-detail", args="t") + "connection/"
        response = client_logged_in.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inspection_bad_ordering_filter(self, client_logged_in):
        """Test ScanJob inspection results with bad ordering filter."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

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

    def test_inspection_bad_status_filter(self, client_logged_in):
        """Test ScanJob inspection results with bad status filter."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

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

    def test_inspection_bad_source_id_filter(self, client_logged_in):
        """Test ScanJob inspection results with bad source_id filter."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

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

    def test_inspection_filter_status(self, client_logged_in):
        """Get ScanJob inspection results with a filtered status."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

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

    def test_inspection_paging(self, client_logged_in):
        """Test paging of ScanJob inspection results."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)

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

    def test_inspection_ordering_by_name(self, client_logged_in):
        """Tests inspection result ordering by name."""
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        # Create an inspection system result
        inspect_sys_result = InspectResult(
            name="Foo1",
            status=SystemConnectionResult.SUCCESS,
            inspect_group=InspectGroupFactory(source=source1),
        )
        inspect_sys_result.save()
        inspect_sys_result.inspect_group.tasks.add(scan_tasks[2])

        inspect_sys_result2 = InspectResult(
            name="Foo2",
            status=SystemConnectionResult.SUCCESS,
            inspect_group=InspectGroupFactory(source=source1),
        )
        inspect_sys_result2.save()
        inspect_sys_result2.inspect_group.tasks.add(scan_tasks[2])

        inspect_sys_result3 = InspectResult(
            name="Foo3",
            status=SystemConnectionResult.FAILED,
            inspect_group=InspectGroupFactory(source=source2),
        )
        inspect_sys_result3.save()
        inspect_sys_result3.inspect_group.tasks.add(scan_tasks[3])

        inspect_sys_result4 = InspectResult(
            name="Foo4",
            status=SystemConnectionResult.FAILED,
            inspect_group=InspectGroupFactory(source=source2),
        )
        inspect_sys_result4.save()
        inspect_sys_result4.inspect_group.tasks.add(scan_tasks[3])

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

    def test_inspection_filter_by_source_id(self, client_logged_in):
        """Tests inspection result filter by source_id."""
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        # Create an inspection system result
        inspect_sys_result = InspectResult(
            name="Foo1",
            status=SystemConnectionResult.SUCCESS,
            inspect_group=InspectGroupFactory(source=source1),
        )
        inspect_sys_result.save()
        inspect_sys_result.inspect_group.tasks.add(scan_tasks[2])

        inspect_sys_result2 = InspectResult(
            name="Foo2",
            status=SystemConnectionResult.SUCCESS,
            inspect_group=InspectGroupFactory(source=source1),
        )
        inspect_sys_result2.save()
        inspect_sys_result2.inspect_group.tasks.add(scan_tasks[2])

        inspect_sys_result3 = InspectResult(
            name="Foo3",
            status=SystemConnectionResult.FAILED,
            inspect_group=InspectGroupFactory(source=source2),
        )
        inspect_sys_result3.save()
        inspect_sys_result3.inspect_group.tasks.add(scan_tasks[3])

        inspect_sys_result4 = InspectResult(
            name="Foo4",
            status=SystemConnectionResult.FAILED,
            inspect_group=InspectGroupFactory(source=source2),
        )
        inspect_sys_result4.save()
        inspect_sys_result4.inspect_group.tasks.add(scan_tasks[3])

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

    def test_inspection_two_tasks(self, client_logged_in):
        """Tests inspection result ordering across tasks."""
        credential = CredentialFactory()
        source1 = SourceFactory(credentials=[credential])
        source2 = SourceFactory(credentials=[credential])
        scan_job, scan_tasks = create_scan_job_two_tasks(
            source1, source2, ScanTask.SCAN_TYPE_INSPECT
        )
        # Create an inspection system result
        inspect_sys_result = InspectResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            inspect_group=InspectGroupFactory(source=source1),
        )
        inspect_sys_result.save()
        inspect_sys_result.inspect_group.tasks.add(scan_tasks[2])

        inspect_sys_result2 = InspectResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            inspect_group=InspectGroupFactory(
                source=source1,
            ),
        )
        inspect_sys_result2.save()
        inspect_sys_result2.inspect_group.tasks.add(scan_tasks[2])

        inspect_sys_result3 = InspectResult(
            name="Foo",
            status=SystemConnectionResult.FAILED,
            inspect_group=InspectGroupFactory(
                source=source2,
            ),
        )
        inspect_sys_result3.save()
        inspect_sys_result3.inspect_group.tasks.add(scan_tasks[3])

        inspect_sys_result4 = InspectResult(
            name="Foo",
            status=SystemConnectionResult.FAILED,
            inspect_group=InspectGroupFactory(
                source=source2,
            ),
        )
        inspect_sys_result4.save()
        inspect_sys_result4.inspect_group.tasks.add(scan_tasks[3])

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

    def test_inspection_results_with_none(self, client_logged_in):
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

    def test_inspection_delete_source(self, client_logged_in):
        """Get ScanJob inspection results after source has been deleted."""
        credential = CredentialFactory()
        source = SourceFactory(credentials=[credential])
        scan_job, scan_task = create_scan_job(source, ScanTask.SCAN_TYPE_INSPECT)
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

    def test_inspection_not_found(self, client_logged_in):
        """Get ScanJob connection results with 404."""
        url = reverse("v1:scanjob-detail", args="2") + "inspection/"
        response = client_logged_in.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_inspection_bad_request(self, client_logged_in):
        """Get ScanJob connection results with 400."""
        url = reverse("v1:scanjob-detail", args="t") + "inspection/"
        response = client_logged_in.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_jobs_not_allowed(self, client_logged_in):
        """Test post jobs not allowed."""
        url = reverse("v1:scanjob-detail", args=(1,))
        url = url[:-2]
        response = client_logged_in.post(url, {})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_not_allowed(self, client_logged_in):
        """Test list all jobs not allowed."""
        url = reverse("v1:scanjob-detail", args=(1,))
        url = url[:-2]
        response = client_logged_in.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_not_allowed(self, client_logged_in):
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
                    "jboss_ws": True,
                }
            },
        }
        url = reverse("v1:scanjob-detail", args=(scan.most_recent_scanjob.id,))
        response = client_logged_in.put(url, data=data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_not_allowed_disable_optional_products(self, client_logged_in):
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
        response = client_logged_in.put(url, data=data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_partial_update(self, client_logged_in):
        """Test partial update not allow for scanjob."""
        scan = ScanFactory()
        scan_job = scan.most_recent_scanjob

        data = {"scan_type": ScanTask.SCAN_TYPE_INSPECT}
        url = reverse("v1:scanjob-detail", args=(scan_job.id,))
        response = client_logged_in.patch(url, data=data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete(self, client_logged_in):
        """Delete a ScanJob is not supported."""
        scan_job = ScanJobFactory()

        url = reverse("v1:scanjob-detail", args=(scan_job.id,))
        response = client_logged_in.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_cancel(self, client_logged_in):
        """Cancel a scanjob."""
        scan_job = ScanJobFactory()
        url = reverse("v1:scanjob-cancel", args=(scan_job.id,))
        response = client_logged_in.put(url)
        assert response.ok

    def test_cancel_bad_id(self, client_logged_in):
        """Cancel a scanjob with bad id."""
        url = reverse("v1:scanjob-cancel", args=("string",))
        response = client_logged_in.put(url)
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
        serializer = ScanJobSerializerV1(scan_job)
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
        serializer = ScanJobSerializerV1(scan_job)
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
        scan_options = {
            "disabled_optional_products": disabled_optional_products_default(),
            "enabled_extended_product_search": (
                enabled_extended_product_search_default()
            ),
        }
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_ws": True,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        json_disabled, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializerV1(scan_job)
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
        scan_options = {
            "disabled_optional_products": disabled_optional_products_default()
        }
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_ws": True,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        json_disabled, _ = scan_options_products(expected_vars)

        serializer = ScanJobSerializerV1(scan_job)
        json_scan = serializer.data
        assert (
            json_scan.get("options").get("disabled_optional_products") == json_disabled
        )
        assert json_scan.get("options").get("enabled_extended_product_search") is None

    def test_get_extra_vars_missing_extended_search(self):
        """Tests the get_extra_vars with disabled products None."""
        scan_options = {
            "enabled_extended_product_search": (
                enabled_extended_product_search_default()
            ),
        }
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_ws": True,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        _, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializerV1(scan_job)
        json_scan = serializer.data
        assert json_scan.get("options").get("disabled_optional_products") is None
        assert (
            json_scan.get("options").get("enabled_extended_product_search")
            == json_enabled_ext
        )

    def test_get_extra_vars_missing_search_directories_empty(self):
        """Tests the get_extra_vars with search_directories empty."""
        search_directories = []
        ScanSerializer.validate_search_directories(search_directories)

    def test_get_extra_vars_missing_search_directories_w_int(self, client_logged_in):
        """Tests the get_extra_vars with search_directories contains int."""
        with pytest.raises(ValidationError):
            ScanSerializer.validate_search_directories([1])

    def test_get_extra_vars_missing_search_directories_w_not_path(
        self, client_logged_in
    ):
        """Tests the get_extra_vars with search_directories no path."""
        with pytest.raises(ValidationError):
            ScanSerializer.validate_search_directories(["a"])

    def test_get_extra_vars_missing_search_directories_w_path(self):
        """Tests the get_extra_vars with search_directories no path."""
        ScanSerializer.validate_search_directories(["/a"])

    def test_get_extra_vars_extended_search(self):
        """Tests the get_extra_vars method with extended search."""
        extended = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_ws": True,
            Scan.EXT_PRODUCT_SEARCH_DIRS: ["a", "b"],
        }
        scan_options = {
            "disabled_optional_products": disabled_optional_products_default(),
            "enabled_extended_product_search": extended,
        }
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_ws": True,
            "jboss_eap_ext": True,
            "jboss_fuse_ext": True,
            "jboss_ws_ext": True,
            "search_directories": "a b",
        }
        assert extra_vars == expected_vars

        json_disabled, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializerV1(scan_job)
        json_scan = serializer.data
        assert (
            json_scan.get("options").get("disabled_optional_products") == json_disabled
        )
        assert json_scan.get("options").get(
            "enabled_extended_product_search"
        ) == json_enabled_ext | {"search_directories": ["a", "b"]}

    def test_get_extra_vars_mixed(self):
        """Tests the get_extra_vars method with mixed values."""
        disabled = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_ws": False,
        }
        scan_options = {
            "disabled_optional_products": disabled,
            "enabled_extended_product_search": (
                enabled_extended_product_search_default()
            ),
        }
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )
        extra_vars = scan_job.get_extra_vars()

        expected_vars = {
            "jboss_eap": True,
            "jboss_fuse": False,
            "jboss_ws": True,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        json_disabled, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializerV1(scan_job)
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
        extended = enabled_extended_product_search_default()
        disabled = {
            "jboss_eap": True,
            "jboss_fuse": True,
            "jboss_ws": True,
        }
        scan_options = {
            "disabled_optional_products": disabled,
            "enabled_extended_product_search": extended,
        }
        scan_job, _ = create_scan_job(
            SourceFactory(), ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
        )

        extra_vars = scan_job.get_extra_vars()

        expected_vars = {
            "jboss_eap": False,
            "jboss_fuse": False,
            "jboss_ws": False,
            "jboss_eap_ext": False,
            "jboss_fuse_ext": False,
            "jboss_ws_ext": False,
        }
        assert extra_vars == expected_vars

        json_disabled, json_enabled_ext = scan_options_products(expected_vars)

        serializer = ScanJobSerializerV1(scan_job)
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
    def test_list_jobs(self, client_logged_in):
        """List all ScanJobs under a scan."""
        scan = ScanFactory(most_recent_scanjob__report=None)
        scan_job = scan.most_recent_scanjob
        # create another scanjob to ensure it wont appear in the filtered list
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

    def test_filtered_list(self, client_logged_in):
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

    def test_delete_scan_cascade(self, client_logged_in):
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
        sys_result = InspectResult.objects.create(
            name="Foo",
            status=InspectResult.SUCCESS,
            inspect_group=InspectGroupFactory(),
        )
        sys_result.inspect_group.tasks.add(scan_task)

        RawFact.objects.create(
            name="fact_key", value="fact_value", inspect_result=sys_result
        )

        scan_job.save()

        job_count = len(scan.jobs.all())
        assert job_count != 0
        url = reverse("v1:scan-detail", args=(scan_id,))
        response = client_logged_in.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        job_count = len(scan.jobs.all())
        assert job_count == 0


@pytest.mark.django_db
class TestScanJobViewSetV2:
    """Test v2 ScanJob ViewSet."""

    @pytest.fixture
    def scanjob(self):
        """Return a inspect scanjob with associated tasks."""
        source = SourceFactory()
        scan = ScanFactory(sources=[source])
        scanjob = scan.most_recent_scanjob
        scanjob.sources.add(source)
        # with the following numbers, we expect count=10, failed=2, scanned=3 and
        # unreachable=5 - see ScanJobQuerySet and it's test for more details
        ScanTaskFactory(
            job=scanjob,
            systems_count=10,
            systems_failed=1,
            systems_scanned=6,
            systems_unreachable=3,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
        )
        ScanTaskFactory(
            job=scanjob,
            systems_count=6,
            systems_failed=1,
            systems_scanned=3,
            systems_unreachable=2,
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
        )
        return scanjob

    def test_retrieve(self, client_logged_in, scanjob):
        """Test retrieving a single ScanJob."""
        source = scanjob.sources.first()
        url = reverse("v2:job-detail", args=(scanjob.id,))
        response = client_logged_in.get(url)
        assert response.ok
        assert response.json() == {
            "id": scanjob.id,
            "end_time": scanjob.end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "report_id": scanjob.report_id,
            "scan_id": scanjob.scan.id,
            "scan_type": scanjob.scan_type,
            "sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type,
                }
            ],
            "start_time": scanjob.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "status": scanjob.status,
            "status_message": scanjob.status_message,
            "systems_count": 10,
            "systems_failed": 2,
            "systems_scanned": 3,
            "systems_unreachable": 5,
        }

    def test_list(self, client_logged_in, scanjob):
        """Test endpoint for listing scanjobs."""
        source = scanjob.sources.first()
        url = reverse("v2:job-list")
        response = client_logged_in.get(url)
        assert response.ok
        assert response.json() == {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": scanjob.id,
                    "end_time": scanjob.end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "report_id": scanjob.report_id,
                    "scan_id": scanjob.scan.id,
                    "scan_type": scanjob.scan_type,
                    "sources": [
                        {
                            "id": source.id,
                            "name": source.name,
                            "source_type": source.source_type,
                        }
                    ],
                    "start_time": scanjob.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "status": scanjob.status,
                    "status_message": scanjob.status_message,
                    "systems_count": 10,
                    "systems_failed": 2,
                    "systems_scanned": 3,
                    "systems_unreachable": 5,
                }
            ],
        }

    def test_max_number_of_queries(
        self, client_logged_in, django_assert_max_num_queries
    ):
        """Ensure ScanJobView don't explode in a ridiculous number of queries."""
        ScanJobFactory.create_batch(100)
        url = reverse("v2:job-list")
        # make sure all annotations and prefetches are working so this view don't have
        # N+1 issues
        with django_assert_max_num_queries(5):
            response = client_logged_in.get(url)
        assert response.ok

    def test_filter_by_scanid(self, client_logged_in, mocker):
        """Test filtering scanjob list view by scan id."""
        scan = ScanFactory()
        scanjob = scan.most_recent_scanjob
        # fingerprint type "scans" don't have an actual scan
        scanjob_scanless = ScanJobFactory(scan=None)
        assert scanjob.scan_id
        assert scanjob_scanless.scan_id is None

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
            scanjob_scanless.id,
            scanjob.id,
        ]
        # filter by scan_id
        response2 = client_logged_in.get(url, {"scan_id": scanjob.scan_id})
        assert response2.ok
        assert response2.json() == {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [mocker.ANY],
        }
        assert response2.json()["results"][0]["id"] == scanjob.id
        assert response2.json()["results"][0]["scan_id"] == scanjob.scan_id
        # filter scanless jobs
        response3 = client_logged_in.get(url, {"scan_id__isnull": True})
        assert response3.ok
        assert response3.json() == {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [mocker.ANY],
        }
        assert response3.json()["results"][0]["id"] == scanjob_scanless.id
        assert response3.json()["results"][0]["scan_id"] is None

    def test_filter_by_scan_type(self, client_logged_in, mocker):
        """Test filtering scanjob list by scan_type."""
        for scan_type, _ in ScanTask.SCANTASK_TYPE_CHOICES:
            ScanJobFactory(scan_type=scan_type)
        # pick a random type for the sake of this test
        chosen_type, _ = random.choice(ScanTask.SCANTASK_TYPE_CHOICES)
        scanjob = ScanJob.objects.get(scan_type=chosen_type)
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
        assert result["id"] == scanjob.id
        assert result["scan_type"] == chosen_type

    def test_filter_by_status(self, client_logged_in, mocker):
        """Test filtering scanjob list by status."""
        for scanjob_status, _ in ScanTask.STATUS_CHOICES:
            ScanJobFactory(status=scanjob_status)
        # pick a random status for the sake of this test
        chosen_status, _ = random.choice(ScanTask.STATUS_CHOICES)
        scanjob = ScanJob.objects.get(status=chosen_status)
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
        assert result["id"] == scanjob.id
        assert result["status"] == chosen_status


@pytest.fixture
def scanjob_with_inspect_results():
    """ScanJob with 3 InspectResults."""
    inspection_results = InspectResultFactory.create_batch(3)
    inspect_groups = InspectGroup.objects.filter(inspect_results__in=inspection_results)
    scanjob = ScanJobFactory(report=None)
    task = ScanTaskFactory(job=scanjob)
    task.inspect_groups.set(inspect_groups)
    return scanjob


@pytest.mark.django_db
def test_delete_inspect_results(scanjob_with_inspect_results: ScanJob):
    """Test ScanJob.delete_inspect_results method."""
    scanjob = scanjob_with_inspect_results
    assert InspectResult.objects.filter(inspect_group__tasks__job=scanjob).exists()
    scanjob.delete_inspect_results()
    assert not InspectResult.objects.filter(inspect_group__tasks__job=scanjob).exists()


@pytest.mark.django_db
def test_delete_inspect_results_bound_to_other_reports(
    scanjob_with_inspect_results: ScanJob,
):
    """Ensure only InspectResults uniquely bound to a ScanJob are deleted."""
    inspect_res = InspectResult.objects.first()
    other_report: Report = ReportFactory()
    inspect_res.inspect_group.reports.add(other_report)
    # save id in a variable so we can check later for existence
    inspect_res_id = inspect_res.id

    scanjob = scanjob_with_inspect_results
    assert InspectResult.objects.filter(inspect_group__tasks__job=scanjob).count() == 3
    scanjob.delete_inspect_results()
    assert InspectResult.objects.filter(inspect_group__tasks__job=scanjob).count() == 1
    assert InspectResult.objects.filter(id=inspect_res_id).exists()
    # deleting the other report should make the results deletable
    other_report.delete()
    scanjob.delete_inspect_results()
    assert InspectResult.objects.filter(inspect_group__tasks__job=scanjob).count() == 0
    assert not InspectResult.objects.filter(id=inspect_res_id).exists()


@pytest.mark.django_db
def test_scanjob_model_str():
    """Test the __str__ method."""
    scan_job = ScanJobFactory()
    scan_job_str = f"{scan_job}"
    assert f"id={scan_job.id}" in scan_job_str
    assert f"scan_type={scan_job.scan_type}" in scan_job_str
    assert f"status={scan_job.status}" in scan_job_str
