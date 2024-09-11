"""Test the report API."""

from functools import partial
from unittest import mock

import pytest
from django.test import override_settings
from rest_framework import status
from rest_framework.reverse import reverse

from api import messages
from api.models import Report, ScanTask
from tests.factories import ReportFactory


@pytest.mark.django_db
class TestAsyncMergeReports:
    """Tests against the Deployment reports function."""

    def merge_details_by_ids(self, data, client_logged_in):
        """Call the create endpoint."""
        return client_logged_in.post(reverse("v1:reports-merge"), data)

    def merge_details_by_ids_expect_201(self, data, client_logged_in):
        """Create a source, return the response as a dict."""
        response = self.merge_details_by_ids(data, client_logged_in)
        assert response.status_code == status.HTTP_201_CREATED, response.json()
        return response.json()

    def merge_details_by_ids_expect_400(self, data, client_logged_in):
        """Create a source, return the response as a dict."""
        response = self.merge_details_by_ids(data, client_logged_in)
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
        return response.json()

    def test_empty_body(self, client_logged_in):
        """Test report merge with empty body."""
        data = ""
        json_response = self.merge_details_by_ids_expect_400(data, client_logged_in)
        assert json_response == {"reports": [messages.REPORT_MERGE_REQUIRED]}

    def test_by_id_merge_empty_dict(self, client_logged_in):
        """Test report merge by id with empty dict."""
        data = {}
        json_response = self.merge_details_by_ids_expect_400(data, client_logged_in)
        assert json_response == {"reports": [messages.REPORT_MERGE_REQUIRED]}

    def test_by_id_merge_jobs_not_list(self, client_logged_in):
        """Test report merge by id with not list."""
        data = {"reports": 5}
        json_response = self.merge_details_by_ids_expect_400(data, client_logged_in)
        assert json_response == {"reports": [messages.REPORT_MERGE_NOT_LIST]}

    def test_by_id_merge_jobs_list_too_short(self, client_logged_in):
        """Test report merge by id with list too short."""
        data = {"reports": [5]}
        json_response = self.merge_details_by_ids_expect_400(data, client_logged_in)
        assert json_response == {"reports": [messages.REPORT_MERGE_TOO_SHORT]}

    def test_by_id_merge_jobs_list_empty(self, client_logged_in):
        """Test report merge by id with an empty list."""
        data = {"reports": []}
        json_response = self.merge_details_by_ids_expect_400(data, client_logged_in)
        assert json_response == {"reports": [messages.REPORT_MERGE_TOO_SHORT]}

    def test_by_id_merge_jobs_list_contains_string(self, client_logged_in):
        """Test report merge by id with containing str."""
        data = {"reports": [5, "hello"]}
        json_response = self.merge_details_by_ids_expect_400(data, client_logged_in)
        assert json_response == {"reports": [messages.REPORT_MERGE_NOT_INT]}

    def test_by_id_merge_jobs_list_contains_duplicates(self, client_logged_in):
        """Test report merge by id with containing duplicates."""
        data = {"reports": [5, 5]}
        json_response = self.merge_details_by_ids_expect_400(data, client_logged_in)
        assert json_response == {"reports": [messages.REPORT_MERGE_NOT_UNIQUE]}

    def test_by_id_merge_jobs_list_contains_invalid_job_ids(self, client_logged_in):
        """Test report merge by id with containing duplicates."""
        data = {"reports": [5, 6]}
        json_response = self.merge_details_by_ids_expect_400(data, client_logged_in)
        assert json_response == {"reports": [messages.REPORT_MERGE_NOT_FOUND % "5, 6"]}

    def test_by_id_merge_jobs_success(self, client_logged_in, mocker):
        """Test report merge by id jobs success."""
        report1 = ReportFactory(generate_raw_facts=True)
        report2 = ReportFactory(generate_raw_facts=True)
        data = {"reports": [report1.id, report2.id]}
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            json_response = self.merge_details_by_ids_expect_201(data, client_logged_in)
        expected = {
            "job_id": mock.ANY,
            "report_id": mock.ANY,
            "scan_id": None,
            "scan_type": "fingerprint",
            "status": "running",
            "status_message": "Job is running.",
        }
        assert json_response == expected
        report = Report.objects.get(id=json_response["report_id"])
        assert report.scanjob.id == json_response["job_id"]
        source_sorter = partial(sorted, key=lambda x: x["source_name"])
        assert source_sorter(report.sources) == source_sorter(
            list(report1.sources) + list(report2.sources)
        )
        scan_job_detail_url = reverse("v2:job-detail", args=(report.scanjob.id,))
        scan_job_response = client_logged_in.get(scan_job_detail_url)

        assert scan_job_response.json() == {
            "id": report.scanjob.id,
            "report_id": report.id,
            "scan_id": None,
            "scan_type": "fingerprint",
            "sources": [],
            "start_time": mocker.ANY,
            "end_time": mocker.ANY,
            "status": ScanTask.COMPLETED,
            "status_message": "Job is complete.",
            "systems_count": 0,
            "systems_failed": 0,
            "systems_scanned": 0,
            "systems_unreachable": 0,
        }
        # finally, make sure the deployments report was created
        report.refresh_from_db()
        assert report.deployment_report_id
