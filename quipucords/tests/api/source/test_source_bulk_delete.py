"""Tests for quipucords.api.source.source_bulk_delete."""
import pytest
from django.urls import reverse
from rest_framework import status

from api.common.util import ALL_IDS_MAGIC_STRING
from api.source.model import Source
from tests.factories import (
    ScanFactory,
    ScanJobFactory,
    ScanTaskFactory,
    SourceFactory,
    generate_invalid_id,
)


@pytest.mark.django_db
class TestSourceBulkDelete:
    """Tests the Source bulk_delete function."""

    def test_bulk_delete_specific_ids(self, client_logged_in):
        """Test that bulk delete deletes all requested sources."""
        source1 = SourceFactory()
        source2 = SourceFactory()
        delete_request = {"ids": [source1.id, source2.id]}
        response = client_logged_in.post(
            reverse("v1:sources-bulk-delete"),
            data=delete_request,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(Source.objects.filter(id__in=[source1.id, source2.id])) == 0

    def test_bulk_delete_all_ids(self, client_logged_in):
        """Test that bulk delete deletes all sources."""
        source1 = SourceFactory()
        source2 = SourceFactory()
        delete_request = {"ids": ALL_IDS_MAGIC_STRING}
        response = client_logged_in.post(
            reverse("v1:sources-bulk-delete"),
            data=delete_request,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(Source.objects.filter(id__in=[source1.id, source2.id])) == 0
        assert Source.objects.count() == 0

    def test_bulk_delete_rejects_invalid_inputs(self, client_logged_in):
        """
        Test that bulk delete rejects unexpected value types in "ids".

        Note: test_set_of_ids_or_all_str covers bad inputs more exhaustively.
        """
        invalid_delete_params = {"ids": []}
        response = client_logged_in.post(
            reverse("v1:sources-bulk-delete"),
            data=invalid_delete_params,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_bulk_delete_ignores_missing_ids(self, client_logged_in, faker):
        """Test bulk delete succeeds and reports missing IDs."""
        source1 = SourceFactory()
        source2 = SourceFactory()
        non_existent_id = generate_invalid_id(faker)
        delete_request = {"ids": [non_existent_id, source1.id, source2.id]}
        response = client_logged_in.post(
            reverse("v1:sources-bulk-delete"),
            data=delete_request,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert set(response_json["deleted"]) == set([source1.id, source2.id])
        assert response_json["missing"] == [non_existent_id]
        assert response_json["skipped"] == []
        assert not Source.objects.filter(pk__in=[source1.id, source2.id]).exists()

    def test_bulk_delete_ignores_errors(self, client_logged_in):
        """Test bulk delete succeeds and reports skipped IDs."""
        source = SourceFactory()
        source_in_use = SourceFactory()
        scan1 = ScanFactory(sources=[source_in_use])
        scan2 = ScanFactory(sources=[source_in_use])
        delete_request = {"ids": [source_in_use.id, source.id]}
        response = client_logged_in.post(
            reverse("v1:sources-bulk-delete"),
            data=delete_request,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["deleted"] == [source.id]
        assert response_json["missing"] == []
        assert len(response_json["skipped"]) == 1
        assert response_json["skipped"][0]["source"] == source_in_use.id
        assert set(response_json["skipped"][0]["scans"]) == set([scan1.id, scan2.id])
        assert not Source.objects.filter(pk=source.id).exists()
        assert Source.objects.filter(pk=source_in_use.id).exists()

    def test_bulk_delete_all(self, client_logged_in):
        """Test bulk delete succeeds with magic "all" token."""
        source1 = SourceFactory()
        source2 = SourceFactory()
        source_in_use1 = SourceFactory()
        scan1 = ScanFactory(sources=[source_in_use1])
        source_in_use2 = SourceFactory()
        scan2 = ScanFactory(sources=[source_in_use2])
        scan2job = ScanJobFactory(scan=scan2)
        scan2job.sources.add(source_in_use2)
        scan2task = ScanTaskFactory(job=scan2job, source=source_in_use2)
        delete_request = {"ids": ALL_IDS_MAGIC_STRING}
        response = client_logged_in.post(
            reverse("v1:sources-bulk-delete"),
            data=delete_request,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert set(response_json["deleted"]) == set([source1.id, source2.id])
        assert response_json["missing"] == []

        # Note that lists like "skipped" may not be sorted.
        expected_skipped = sorted(
            [
                {
                    "source": source_in_use1.id,
                    "scans": [scan1.id],
                    "scanjobs": [],
                    "scantasks": [],
                },
                {
                    "source": source_in_use2.id,
                    "scans": [scan2.id],
                    "scanjobs": [scan2job.id],
                    "scantasks": [scan2task.id],
                },
            ],
            key=lambda skipped: skipped["source"],
        )
        actual_skipped = sorted(
            response_json["skipped"], key=lambda skipped: skipped["source"]
        )
        assert expected_skipped == actual_skipped

        assert not Source.objects.exclude(
            pk__in=[source_in_use1.id, source_in_use2.id]
        ).exists()
        assert Source.objects.filter(
            pk__in=[source_in_use1.id, source_in_use2.id]
        ).exists()
