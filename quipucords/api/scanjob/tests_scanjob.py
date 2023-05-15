"""Test the API application."""

# pylint: disable=unused-argument,invalid-name,too-many-lines

import json
from unittest.mock import patch

from django.core import management
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api import messages
from api.models import (
    Credential,
    DisabledOptionalProductsOptions,
    ExtendedProductSearchOptions,
    RawFact,
    Scan,
    ScanJob,
    ScanOptions,
    ScanTask,
    ServerInformation,
    Source,
    SystemConnectionResult,
    SystemInspectionResult,
)
from api.scan.serializer import ExtendedProductSearchOptionsSerializer
from api.scanjob.serializer import ScanJobSerializer
from api.scanjob.view import expand_scanjob
from scanner.test_util import create_scan_job, create_scan_job_two_tasks


def dummy_start():
    """Create a dummy method for testing."""


class ScanJobTest(TestCase):
    """Test the basic ScanJob infrastructure."""

    def setUp(self):
        """Create test setup."""
        management.call_command("flush", "--no-input")
        self.server_id = ServerInformation.create_or_retrieve_server_id()
        self.cred = Credential.objects.create(
            name="cred1",
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.cred_for_upload = self.cred.id

        self.source = Source(name="source1", source_type="network", port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

        self.connect_scan = Scan.objects.create(
            name="connect_test", scan_type=ScanTask.SCAN_TYPE_CONNECT
        )
        self.connect_scan.sources.add(self.source)

        self.inspect_scan = Scan.objects.create(name="inspect_test")
        self.inspect_scan.sources.add(self.source)

    def create_job_expect_201(self, scan_id):
        """Create a scan, return the response as a dict."""
        url = reverse("scan-detail", args=(scan_id,)) + "jobs/"
        response = self.client.post(url, {}, "application/json")
        response_json = response.json()
        if response.status_code != status.HTTP_201_CREATED:
            print("Cause of failure: ")
            print(response_json)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response_json

    def test_queue_task(self):
        """Test create queue state change."""
        # Cannot use util because its testing queue
        # Create scan configuration
        scan = Scan.objects.create(name="test", scan_type=ScanTask.SCAN_TYPE_INSPECT)

        # Add source to scan
        scan.sources.add(self.source)

        options_to_use = ScanOptions.objects.create()

        scan.options = options_to_use
        scan.save()

        # Create Job
        scan_job = ScanJob.objects.create(scan=scan)

        # Job in created state
        self.assertEqual(scan_job.status, ScanTask.CREATED)
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 0)

        # Queue job to run
        scan_job.queue()

        # Job should be in pending state
        self.assertEqual(scan_job.status, ScanTask.PENDING)

        # Queue should have created scan tasks
        tasks = scan_job.tasks.all().order_by("sequence_number")
        self.assertEqual(len(tasks), 3)

        # Validate connect task created and correct
        connect_task = tasks[0]
        self.assertEqual(connect_task.scan_type, ScanTask.SCAN_TYPE_CONNECT)
        self.assertEqual(connect_task.status, ScanTask.PENDING)

        # Validate inspect task created and correct
        inspect_task = tasks[1]
        self.assertEqual(inspect_task.scan_type, ScanTask.SCAN_TYPE_INSPECT)
        self.assertEqual(inspect_task.status, ScanTask.PENDING)

    def test_queue_invalid_state_changes(self):
        """Test create queue failed."""
        scan_job, _ = create_scan_job(self.source, scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan_job.status = ScanTask.FAILED

        # Queue job to run
        scan_job.queue()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.complete()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.status_pause()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.status_start()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.cancel()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.status_restart()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.fail("test failure")
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.status = ScanTask.CREATED
        scan_job.fail("test failure")
        self.assertEqual(scan_job.status, ScanTask.CREATED)

        scan_job.status = ScanTask.RUNNING
        scan_job.complete()
        self.assertEqual(scan_job.status, ScanTask.COMPLETED)

    def test_start_task(self):
        """Test start pending task."""
        scan_job, _ = create_scan_job(self.source, scan_type=ScanTask.SCAN_TYPE_CONNECT)

        # Job in created state
        tasks = scan_job.tasks.all()

        # Queue job to run
        scan_job.queue()
        self.assertEqual(scan_job.status, ScanTask.PENDING)

        # Queue should have created scan tasks
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 1)

        # Start job
        scan_job.status_start()

    def test_pause_restart_task(self):
        """Test pause and restart task."""
        scan_job, _ = create_scan_job(self.source, scan_type=ScanTask.SCAN_TYPE_CONNECT)

        # Queue job to run
        scan_job.queue()
        self.assertEqual(scan_job.status, ScanTask.PENDING)

        # Queue should have created scan tasks
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 1)
        connect_task = scan_job.tasks.first()  # pylint: disable=no-member
        self.assertEqual(connect_task.status, ScanTask.PENDING)

        # Start job
        scan_job.status_start()
        self.assertEqual(scan_job.status, ScanTask.RUNNING)

        scan_job.status_pause()
        connect_task = scan_job.tasks.first()  # pylint: disable=no-member
        self.assertEqual(scan_job.status, ScanTask.PAUSED)
        self.assertEqual(connect_task.status, ScanTask.PAUSED)

        scan_job.status_restart()
        connect_task = scan_job.tasks.first()  # pylint: disable=no-member
        self.assertEqual(scan_job.status, ScanTask.PENDING)
        self.assertEqual(connect_task.status, ScanTask.PENDING)

        scan_job.cancel()
        connect_task = scan_job.tasks.first()  # pylint: disable=no-member
        self.assertEqual(scan_job.status, ScanTask.CANCELED)
        self.assertEqual(connect_task.status, ScanTask.CANCELED)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_successful_create(self, start_scan):
        """A valid create request should succeed."""
        response = self.create_job_expect_201(self.connect_scan.id)
        self.assertIn("id", response)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_retrieve(self, start_scan):
        """Get ScanJob details by primary key."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse("scanjob-detail", args=(initial["id"],))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("scan", response.json())
        scan = response.json()["scan"]

        self.assertEqual(scan, {"id": 1, "name": "connect_test"})

    def test_retrieve_bad_id(self):
        """Get ScanJob details by bad primary key."""
        url = reverse("scanjob-detail", args=("string",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_connection(self):
        """Get ScanJob connection results."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Foo",
                    "status": "success",
                    "credential": {"id": 1, "name": "cred1"},
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                }
            ],
        }
        self.assertEqual(json_response, expected)

    def test_connection_bad_ordering_filter(self):
        """Test ScanJob connection results with bad ordering filter."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()
        bad_param = "bad_param"
        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        url += "?ordering=" + bad_param
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_connection_bad_status_filter(self):
        """Test ScanJob connection results with bad status filter."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()
        bad_param = "bad_param"
        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        url += "?status=" + bad_param
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_connection_bad_source_id_filter(self):
        """Test ScanJob connection results with bad source_id filter."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()
        bad_param = "bad_param"
        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        url += "?source_id=" + bad_param
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_connection_filter_status(self):
        """Get ScanJob connection results with a filtered status."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        url += "?status=" + SystemConnectionResult.FAILED
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {"count": 0, "next": None, "previous": None, "results": []}
        self.assertEqual(json_response, expected)

    def test_connection_failed_success(self):
        """Get ScanJob connection results for multiple systems."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create two connection system results one failure & one success
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()
        sys_result = SystemConnectionResult(
            name="Bar",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result,
        )
        sys_result.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Bar",
                    "status": "failed",
                    "credential": {"id": 1, "name": "cred1"},
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                },
                {
                    "name": "Foo",
                    "status": "success",
                    "credential": {"id": 1, "name": "cred1"},
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                },
            ],
        }

        self.assertEqual(json_response, expected)

    def test_connection_name_ordering(self):
        """Get ScanJob connection results for systems ordered by name."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create two connection system results one failure & one success
        conn_result = scan_task.prerequisites.first().connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()
        sys_result = SystemConnectionResult(
            name="Bar",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result,
        )
        sys_result.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        url += "?ordering=-name"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Foo",
                    "status": "success",
                    "credential": {"id": 1, "name": "cred1"},
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                },
                {
                    "name": "Bar",
                    "status": "failed",
                    "credential": {"id": 1, "name": "cred1"},
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                },
            ],
        }

        self.assertEqual(json_response, expected)

    def test_connection_two_scan_tasks(self):
        """Get ScanJob connection results for multiple tasks."""
        # pylint: disable=no-member
        # create a second source:
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        source2.credentials.add(self.cred)
        scan_job, scan_tasks = create_scan_job_two_tasks(
            self.source, source2, ScanTask.SCAN_TYPE_CONNECT
        )

        # Create two connection system results one failure & one success
        conn_result = scan_tasks[0].connection_result
        conn_result2 = scan_tasks[1].connection_result

        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result.save()
        sys_result = SystemConnectionResult(
            name="Bar",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result,
        )
        sys_result.save()
        sys_result = SystemConnectionResult(
            name="Woot",
            source=source2,
            credential=self.cred,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result2,
        )
        sys_result.save()
        sys_result = SystemConnectionResult(
            name="Ness",
            source=source2,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result2,
        )
        sys_result.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 4,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Bar",
                    "status": "failed",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
                {
                    "name": "Woot",
                    "status": "failed",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
                {
                    "name": "Foo",
                    "status": "success",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
                {
                    "name": "Ness",
                    "status": "success",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
            ],
        }

        self.assertEqual(json_response, expected)

    def test_connection_filter_by_source_id(self):
        """Get ScanJob connection results filter by source_id."""
        # pylint: disable=no-member
        # create a second source:
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        source2.credentials.add(self.cred)
        scan_job, scan_tasks = create_scan_job_two_tasks(
            self.source, source2, ScanTask.SCAN_TYPE_CONNECT
        )

        # Create two connection system results one failure & one success
        conn_result = scan_tasks[0].connection_result
        conn_result2 = scan_tasks[1].connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result2 = SystemConnectionResult(
            name="Bar",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result,
        )
        sys_result3 = SystemConnectionResult(
            name="Woot",
            source=source2,
            credential=self.cred,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result2,
        )
        sys_result4 = SystemConnectionResult(
            name="Ness",
            source=source2,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result2,
        )
        sys_result.save()
        sys_result2.save()
        sys_result3.save()
        sys_result4.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        url += "?source_id=" + str(source2.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Woot",
                    "status": "failed",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
                {
                    "name": "Ness",
                    "status": "success",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
            ],
        }

        self.assertEqual(json_response, expected)

    def test_connection_paging(self):
        """Test paging for scanjob connection results."""
        # pylint: disable=no-member
        # create a second source:
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        source2.credentials.add(self.cred)
        scan_job, scan_tasks = create_scan_job_two_tasks(
            self.source, source2, ScanTask.SCAN_TYPE_CONNECT
        )

        # Create two connection system results one failure & one success
        conn_result = scan_tasks[0].connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result2 = SystemConnectionResult(
            name="Bar",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result,
        )
        conn_result2 = scan_tasks[1].connection_result
        sys_result3 = SystemConnectionResult(
            name="Woot",
            source=source2,
            credential=self.cred,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result2,
        )
        sys_result4 = SystemConnectionResult(
            name="Ness",
            source=source2,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result2,
        )
        sys_result.save()
        sys_result2.save()
        sys_result3.save()
        sys_result4.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/?page_size=2"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 4,
            "next": "http://testserver/api/v1/"
            + "jobs/1/connection/?page=2&page_size=2",
            "previous": None,
            "results": [
                {
                    "name": "Bar",
                    "status": "failed",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
                {
                    "name": "Woot",
                    "status": "failed",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
            ],
        }

        self.assertEqual(json_response, expected)

    def test_connection_results_with_none(self):
        """Test connection results with no results for one task."""
        # pylint: disable=no-member
        # create a second source:
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        source2.credentials.add(self.cred)
        scan_job, scan_tasks = create_scan_job_two_tasks(
            self.source, source2, ScanTask.SCAN_TYPE_CONNECT
        )

        # Create two connection system results one failure & one success
        conn_result = scan_tasks[0].connection_result
        sys_result = SystemConnectionResult(
            name="Foo",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.SUCCESS,
            task_connection_result=conn_result,
        )
        sys_result2 = SystemConnectionResult(
            name="Bar",
            source=self.source,
            credential=self.cred,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result,
        )
        sys_result.save()
        sys_result2.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Bar",
                    "status": "failed",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
                {
                    "name": "Foo",
                    "status": "success",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "credential": {"id": 1, "name": "cred1"},
                },
            ],
        }

        self.assertEqual(json_response, expected)

    def test_connection_delete_source_and_cred(self):
        """Get ScanJob connection results after source & cred are deleted."""
        # pylint: disable=no-member
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        cred2 = Credential.objects.create(
            name="cred2",
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        source2.credentials.add(cred2)
        scan_job, scan_task = create_scan_job(source2, ScanTask.SCAN_TYPE_CONNECT)

        # Create a connection system result
        conn_result = scan_task.connection_result
        sys_result = SystemConnectionResult(
            name="Woot",
            source=source2,
            credential=cred2,
            status=SystemConnectionResult.FAILED,
            task_connection_result=conn_result,
        )
        sys_result.save()
        source2.delete()
        cred2.delete()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "connection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [{"name": "Woot", "status": "failed", "source": "deleted"}],
        }
        self.assertEqual(json_response, expected)

    def test_connection_not_found(self):
        """Get ScanJob connection results with 404."""
        # pylint: disable=no-member
        url = reverse("scanjob-detail", args="2") + "connection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_connection_bad_request(self):
        """Get ScanJob connection results with 400."""
        # pylint: disable=no-member
        url = reverse("scanjob-detail", args="t") + "connection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inspection_bad_ordering_filter(self):
        """Test ScanJob inspection results with bad ordering filter."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=self.source,
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
        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/"
        url += "?ordering=" + bad_param
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inspection_bad_status_filter(self):
        """Test ScanJob inspection results with bad status filter."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=self.source,
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
        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/"
        url += "?status=" + bad_param
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inspection_bad_source_id_filter(self):
        """Test ScanJob inspection results with bad source_id filter."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=self.source,
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
        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/"
        url += "?source_id=" + bad_param
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inspection_filter_status(self):
        """Get ScanJob inspection results with a filtered status."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=self.source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/"
        url += "?status=" + SystemConnectionResult.FAILED
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {"count": 0, "next": None, "previous": None, "results": []}
        self.assertEqual(json_response, expected)

    def test_inspection_paging(self):
        """Test paging of ScanJob inspection results."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=self.source,
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
            source=self.source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result2.save()

        fact2 = RawFact(
            name="fact_key2",
            value="fact_value2",
            system_inspection_result=inspect_sys_result2,
        )
        fact2.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/?page_size=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 2,
            "next": "http://testserver/api/v1/jobs/1/inspection/" "?page=2&page_size=1",
            "previous": None,
            "results": [
                {
                    "name": "Foo",
                    "status": "failed",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "facts": [{"name": "fact_key2", "value": "fact_value2"}],
                }
            ],
        }
        self.assertEqual(json_response, expected)

    def test_inspection_ordering_by_name(self):
        """Tests inspection result ordering by name."""
        # pylint: disable=too-many-locals
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        source2.credentials.add(self.cred)
        scan_job, scan_tasks = create_scan_job_two_tasks(
            self.source, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        inspection_result = scan_tasks[2].inspection_result
        inspection_result2 = scan_tasks[3].inspection_result
        # Create an inspection system result
        inspect_sys_result = SystemInspectionResult(
            name="Foo1",
            status=SystemConnectionResult.SUCCESS,
            source=self.source,
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
            source=self.source,
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

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/"
        url += "?ordering=-name"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 4,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Foo4",
                    "status": "failed",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "facts": [],
                },
                {
                    "name": "Foo3",
                    "status": "failed",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "facts": [],
                },
                {
                    "name": "Foo2",
                    "status": "success",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "facts": [{"name": "fact_key2", "value": "fact_value2"}],
                },
                {
                    "name": "Foo1",
                    "status": "success",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "facts": [{"name": "fact_key", "value": "fact_value"}],
                },
            ],
        }
        self.assertEqual(json_response, expected)

    def test_inspection_filter_by_source_id(self):
        """Tests inspection result filter by source_id."""
        # pylint: disable=too-many-locals
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        source2.credentials.add(self.cred)
        scan_job, scan_tasks = create_scan_job_two_tasks(
            self.source, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        # Create an inspection system result
        inspection_result = scan_tasks[2].inspection_result
        inspection_result2 = scan_tasks[3].inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo1",
            status=SystemConnectionResult.SUCCESS,
            source=self.source,
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
            source=self.source,
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

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/"
        url += "?source_id=" + str(source2.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_resp = response.json()
        expected = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Foo3",
                    "status": "failed",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "facts": [],
                },
                {
                    "name": "Foo4",
                    "status": "failed",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "facts": [],
                },
            ],
        }
        diff = [x for x in expected["results"] if x not in json_resp["results"]]
        self.assertEqual(diff, [])

    def test_inspection_two_tasks(self):
        """Tests inspection result ordering across tasks."""
        # pylint: disable=too-many-locals
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        source2.credentials.add(self.cred)
        scan_job, scan_tasks = create_scan_job_two_tasks(
            self.source, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        # Create an inspection system result
        inspection_result = scan_tasks[2].inspection_result
        inspection_result2 = scan_tasks[3].inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=self.source,
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
            source=self.source,
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

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 4,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Foo",
                    "status": "failed",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "facts": [],
                },
                {
                    "name": "Foo",
                    "status": "failed",
                    "source": {"id": 2, "name": "source2", "source_type": "network"},
                    "facts": [],
                },
                {
                    "name": "Foo",
                    "status": "success",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "facts": [{"name": "fact_key", "value": "fact_value"}],
                },
                {
                    "name": "Foo",
                    "status": "success",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "facts": [{"name": "fact_key2", "value": "fact_value2"}],
                },
            ],
        }
        self.assertEqual(json_response, expected)

    def test_inspection_results_with_none(self):
        """Tests inspection results with none for one task."""
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        source2.credentials.add(self.cred)
        scan_job, scan_tasks = create_scan_job_two_tasks(
            self.source, source2, ScanTask.SCAN_TYPE_INSPECT
        )

        # Create an inspection system result
        inspection_result = scan_tasks[2].inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.FAILED,
            source=self.source,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "name": "Foo",
                    "status": "failed",
                    "source": {"id": 1, "name": "source1", "source_type": "network"},
                    "facts": [{"name": "fact_key", "value": "fact_value"}],
                }
            ],
        }
        self.assertEqual(json_response, expected)

    def test_inspection_delete_source(self):
        """Get ScanJob inspection results after source has been deleted."""
        # pylint: disable=no-member
        source2 = Source(name="source2", source_type="network", port=22)
        source2.save()
        source2.credentials.add(self.cred)
        scan_job, scan_task = create_scan_job(source2, ScanTask.SCAN_TYPE_INSPECT)

        # Create an inspection system result
        inspection_result = scan_task.inspection_result
        inspect_sys_result = SystemInspectionResult(
            name="Foo",
            status=SystemConnectionResult.SUCCESS,
            source=source2,
            task_inspection_result=inspection_result,
        )
        inspect_sys_result.save()

        fact = RawFact(
            name="fact_key",
            value="fact_value",
            system_inspection_result=inspect_sys_result,
        )
        fact.save()

        source2.delete()

        url = reverse("scanjob-detail", args=(scan_job.id,)) + "inspection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
        self.assertEqual(json_response, expected)

    def test_inspection_not_found(self):
        """Get ScanJob connection results with 404."""
        # pylint: disable=no-member
        url = reverse("scanjob-detail", args="2") + "inspection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inspection_bad_request(self):
        """Get ScanJob connection results with 400."""
        # pylint: disable=no-member
        url = reverse("scanjob-detail", args="t") + "inspection/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_jobs_not_allowed(self):
        """Test post jobs not allowed."""
        url = reverse("scanjob-detail", args=(1,))
        url = url[:-2]
        response = self.client.post(url, {}, "application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_not_allowed(self):
        """Test list all jobs not allowed."""
        url = reverse("scanjob-detail", args=(1,))
        url = url[:-2]
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_update_not_allowed(self, start_scan):
        """Test update scanjob not allowed."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        data = {
            "sources": [self.source.id],
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
        url = reverse("scanjob-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_update_not_allowed_disable_optional_products(self, start_scan):
        """Test update scan job options not allowed."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        data = {
            "sources": [self.source.id],
            "scan_type": ScanTask.SCAN_TYPE_INSPECT,
            "options": {"disabled_optional_products": "bar"},
        }
        url = reverse("scanjob-detail", args=(initial["id"],))
        response = self.client.put(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_partial_update(self, start_scan):
        """Test partial update not allow for scanjob."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        data = {"scan_type": ScanTask.SCAN_TYPE_INSPECT}
        url = reverse("scanjob-detail", args=(initial["id"],))
        response = self.client.patch(
            url, json.dumps(data), content_type="application/json", format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_delete(self, start_scan):
        """Delete a ScanJob is not supported."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse("scanjob-detail", args=(initial["id"],))
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_pause_bad_state(self, start_scan):
        """Pause a scanjob."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse("scanjob-detail", args=(initial["id"],))
        pause_url = f"{url}pause/"
        response = self.client.put(pause_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pause_bad_id(self):
        """Pause a scanjob with bad id."""
        url = reverse("scanjob-detail", args=("string",))
        pause_url = f"{url}pause/"
        response = self.client.put(pause_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_cancel(self, start_scan):
        """Cancel a scanjob."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse("scanjob-detail", args=(initial["id"],))
        pause_url = f"{url}cancel/"
        response = self.client.put(pause_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancel_bad_id(self):
        """Cancel a scanjob with bad id."""
        url = reverse("scanjob-detail", args=("string",))
        pause_url = f"{url}cancel/"
        response = self.client.put(pause_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_restart_bad_state(self, start_scan):
        """Restart a scanjob."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse("scanjob-detail", args=(initial["id"],))
        pause_url = f"{url}restart/"
        response = self.client.put(pause_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restart_bad_id(self):
        """Restart a scanjob with bad id."""
        url = reverse("scanjob-detail", args=("string",))
        pause_url = f"{url}restart/"
        response = self.client.put(pause_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expand_scanjob(self):
        """Test view expand_scanjob."""
        scan_job, scan_task = create_scan_job(
            self.source, scan_type=ScanTask.SCAN_TYPE_INSPECT
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

        self.assertEqual(json_scan.get("systems_count"), 2)
        self.assertEqual(json_scan.get("systems_failed"), 1)
        self.assertEqual(json_scan.get("systems_scanned"), 1)

    def test_get_extra_vars(self):
        """Tests the get_extra_vars method with empty dict."""
        extended = ExtendedProductSearchOptions.objects.create()
        disabled = DisabledOptionalProductsOptions.objects.create()
        scan_options = ScanOptions.objects.create(
            disabled_optional_products=disabled,
            enabled_extended_product_search=extended,
        )
        scan_job, _ = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
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
        self.assertEqual(extra_vars, expected_vars)

    def test_get_extra_vars_missing_disable_product(self):
        """Tests the get_extra_vars with extended search None."""
        disabled = DisabledOptionalProductsOptions.objects.create()
        scan_options = ScanOptions.objects.create(disabled_optional_products=disabled)
        scan_job, _ = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
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
        self.assertEqual(extra_vars, expected_vars)

    def test_get_extra_vars_missing_extended_search(self):
        """Tests the get_extra_vars with disabled products None."""
        extended = ExtendedProductSearchOptions.objects.create()
        scan_options = ScanOptions.objects.create(
            enabled_extended_product_search=extended
        )
        scan_job, _ = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
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
        self.assertEqual(extra_vars, expected_vars)

    def test_get_extra_vars_missing_search_directories_empty(self):
        """Tests the get_extra_vars with search_directories empty."""
        extended = {"search_directories": []}
        serializer = ExtendedProductSearchOptionsSerializer(data=extended)
        is_valid = serializer.is_valid()
        self.assertTrue(is_valid)

    def test_get_extra_vars_missing_search_directories_w_int(self):
        """Tests the get_extra_vars with search_directories contains int."""
        extended = {"search_directories": [1]}
        serializer = ExtendedProductSearchOptionsSerializer(data=extended)
        is_valid = serializer.is_valid()
        self.assertFalse(is_valid)

    def test_get_extra_vars_missing_search_directories_w_not_path(self):
        """Tests the get_extra_vars with search_directories no path."""
        extended = {"search_directories": ["a"]}
        serializer = ExtendedProductSearchOptionsSerializer(data=extended)
        is_valid = serializer.is_valid()
        self.assertFalse(is_valid)

    def test_get_extra_vars_missing_search_directories_w_path(self):
        """Tests the get_extra_vars with search_directories no path."""
        extended = {"search_directories": ["/a"]}
        serializer = ExtendedProductSearchOptionsSerializer(data=extended)
        is_valid = serializer.is_valid()
        self.assertTrue(is_valid)

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
            self.source, ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
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
        self.assertEqual(extra_vars, expected_vars)

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
            self.source, ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
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
        self.assertEqual(extra_vars, expected_vars)

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
            self.source, ScanTask.SCAN_TYPE_INSPECT, scan_options=scan_options
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
        self.assertEqual(extra_vars, expected_vars)

    # ############################################################
    # # Scan Job tests /jobs path
    # ############################################################
    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_list_jobs(self, start_scan):
        """List all ScanJobs under a scan."""
        self.create_job_expect_201(self.inspect_scan.id)
        self.create_job_expect_201(self.connect_scan.id)

        url = reverse("scan-detail", args=(self.inspect_scan.id,)) + "jobs/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        results1 = [
            {
                "id": 1,
                "scan": {"id": 2, "name": "inspect_test"},
                "scan_type": ScanTask.SCAN_TYPE_INSPECT,
                "status": "created",
                "status_message": messages.SJ_STATUS_MSG_CREATED,
            }
        ]
        expected = {"count": 1, "next": None, "previous": None, "results": results1}
        self.assertEqual(content, expected)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_filtered_list(self, start_scan):
        """List filtered ScanJob objects."""
        self.create_job_expect_201(self.inspect_scan.id)

        url = reverse("scan-detail", args=(self.inspect_scan.id,)) + "jobs/"

        response = self.client.get(url, {"status": ScanTask.PENDING})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        expected = {"count": 0, "next": None, "previous": None, "results": []}
        self.assertEqual(content, expected)

        response = self.client.get(url, {"status": ScanTask.CREATED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        results1 = [
            {
                "id": 1,
                "scan": {"id": 2, "name": "inspect_test"},
                "scan_type": ScanTask.SCAN_TYPE_INSPECT,
                "status": "created",
                "status_message": messages.SJ_STATUS_MSG_CREATED,
            }
        ]
        expected = {"count": 1, "next": None, "previous": None, "results": results1}
        self.assertEqual(content, expected)

    @patch("api.scan.view.start_scan", side_effect=dummy_start)
    def test_delete_scan_cascade(self, start_scan):
        """Delete a scan and its related data."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source, ScanTask.SCAN_TYPE_INSPECT)

        scan = scan_job.scan
        scan_id = scan.id

        self.create_job_expect_201(scan_id)

        # Create a connection system result
        conn_result = scan_task.prerequisites.first().connection_result
        SystemConnectionResult.objects.create(
            name="Foo",
            credential=self.cred,
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
        self.assertNotEqual(job_count, 0)
        url = reverse("scan-detail", args=(scan_id,))
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        job_count = len(scan.jobs.all())
        self.assertEqual(job_count, 0)
