"""
Tests for quipucords.api.scan.view.scan_bulk_delete.

Several tests in TestScanBulkDelete overlap significantly with tests in
TestSourceBulkDelete and TestCredentialBulkDelete because their underlying
functionality is very similar.

@TODO abstract bulk delete logic tests and deduplicate their code (DRY!)
"""
import pytest
from django.urls import reverse
from rest_framework import status

from api.common.util import ALL_IDS_MAGIC_STRING
from api.scan.model import Scan
from api.scanjob.model import ScanJob
from tests.factories import (
    ReportFactory,
    ScanFactory,
    ScanJobFactory,
    ScanTaskFactory,
    generate_invalid_id,
)


@pytest.mark.django_db
class TestScanBulkDelete:
    """Tests the Scan bulk_delete function."""

    def test_bulk_delete_specific_ids(self, client_logged_in):
        """Test that bulk delete deletes all requested scans."""
        scan1 = ScanFactory()
        scan2 = ScanFactory()
        delete_request = {"ids": [scan1.id, scan2.id]}
        response = client_logged_in.post(
            reverse("v1:scans-bulk-delete"),
            data=delete_request,
        )
        assert response.ok
        assert len(Scan.objects.filter(id__in=[scan1.id, scan2.id])) == 0

    def test_bulk_delete_all_ids(self, client_logged_in):
        """Test that bulk delete deletes all scans."""
        scan1 = ScanFactory()
        scan2 = ScanFactory()
        delete_request = {"ids": ALL_IDS_MAGIC_STRING}
        response = client_logged_in.post(
            reverse("v1:scans-bulk-delete"),
            data=delete_request,
        )
        assert response.ok
        assert len(Scan.objects.filter(id__in=[scan1.id, scan2.id])) == 0
        assert Scan.objects.count() == 0

    def test_bulk_delete_rejects_invalid_inputs(self, client_logged_in):
        """
        Test that bulk delete rejects unexpected value types in "ids".

        Note: test_set_of_ids_or_all_str covers bad inputs more exhaustively.
        """
        invalid_delete_params = {"ids": []}
        response = client_logged_in.post(
            reverse("v1:scans-bulk-delete"),
            data=invalid_delete_params,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_bulk_delete_ignores_missing_ids(self, client_logged_in, faker):
        """Test bulk delete succeeds and reports missing IDs."""
        scan1 = ScanFactory()
        scan2 = ScanFactory()
        non_existent_id = generate_invalid_id(faker)
        delete_request = {"ids": [non_existent_id, scan1.id, scan2.id]}
        response = client_logged_in.post(
            reverse("v1:scans-bulk-delete"),
            data=delete_request,
        )
        assert response.ok
        response_json = response.json()
        assert set(response_json["deleted"]) == set([scan1.id, scan2.id])
        assert response_json["missing"] == [non_existent_id]
        assert not Scan.objects.filter(pk__in=[scan1.id, scan2.id]).exists()

    def test_bulk_delete_ignores_errors(self, client_logged_in):
        """Test bulk delete succeeds and deletes related objects."""
        scan1 = ScanFactory()
        scan2_in_use = ScanFactory()
        scan2report = ReportFactory(scanjob=None)
        scan2job = ScanJobFactory(scan=scan2_in_use, report=scan2report)
        scan2task = ScanTaskFactory(job=scan2job)
        delete_request = {"ids": [scan2_in_use.id, scan1.id]}
        response = client_logged_in.post(
            reverse("v1:scans-bulk-delete"),
            data=delete_request,
        )
        assert response.ok
        response_json = response.json()
        assert set(response_json["deleted"]) == {scan1.id, scan2_in_use.id}
        assert response_json["missing"] == []
        assert not Scan.objects.filter(pk__in=[scan1.id, scan2_in_use.id]).exists()

        # Deleting a scan should clean up its jobs and tasks.
        with pytest.raises(scan2job.DoesNotExist):
            scan2job.refresh_from_db()
        with pytest.raises(scan2task.DoesNotExist):
            scan2task.refresh_from_db()
        # However, its report is orphaned and breaks its link to the job.
        # This is a "legacy" behavior that I'm not too happy with.
        # Maybe we should change that and clear objects better in the future.
        # TODO Maybe deleting a scan/task/job should also delete its reports.
        scan2report.refresh_from_db()
        with pytest.raises(ScanJob.DoesNotExist):
            assert scan2report.scanjob

    def test_bulk_delete_all(self, client_logged_in):
        """Test bulk delete succeeds with magic "all" token."""
        scan1 = ScanFactory()
        scan2_in_use = ScanFactory()
        ScanJobFactory(scan=scan2_in_use)

        delete_request = {"ids": ALL_IDS_MAGIC_STRING}
        response = client_logged_in.post(
            reverse("v1:scans-bulk-delete"),
            data=delete_request,
        )
        assert response.ok
        response_json = response.json()
        assert set(response_json["deleted"]) == {
            scan1.id,
            scan2_in_use.id,
        }
        assert response_json["missing"] == []

        assert not Scan.objects.filter(pk__in=[scan1.id, scan2_in_use.id]).exists()
