"""
Tests for quipucords.api.source.view.source_bulk_delete.

Several tests in TestSourceBulkDelete overlap significantly with tests in
TestScanBulkDelete and TestCredentialBulkDelete because their underlying
functionality is very similar.

@TODO abstract bulk delete logic tests and deduplicate their code (DRY!)
"""

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


@pytest.mark.django_db(transaction=True)
class TestSourceBulkDelete:
    """Tests the Source bulk_delete function."""

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_bulk_delete_specific_ids(self, client_logged_in, version):
        """Test that bulk delete deletes all requested sources."""
        source1 = SourceFactory()
        source2 = SourceFactory()
        delete_request = {"ids": [source1.id, source2.id]}
        url = reverse(f"{version}:source-bulk-delete")
        response = client_logged_in.post(url, data=delete_request)
        assert response.ok
        assert len(Source.objects.filter(id__in=[source1.id, source2.id])) == 0

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_bulk_delete_all_ids(self, client_logged_in, version):
        """Test that bulk delete deletes all sources."""
        source1 = SourceFactory()
        source2 = SourceFactory()
        delete_request = {"ids": ALL_IDS_MAGIC_STRING}
        url = reverse(f"{version}:source-bulk-delete")
        response = client_logged_in.post(url, data=delete_request)
        assert response.ok
        assert len(Source.objects.filter(id__in=[source1.id, source2.id])) == 0
        assert Source.objects.count() == 0

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_bulk_delete_rejects_invalid_inputs(self, client_logged_in, version):
        """
        Test that bulk delete rejects unexpected value types in "ids".

        Note: test_set_of_ids_or_all_str covers bad inputs more exhaustively.
        """
        invalid_delete_params = {"ids": []}
        url = reverse(f"{version}:source-bulk-delete")
        response = client_logged_in.post(url, data=invalid_delete_params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_bulk_delete_ignores_missing_ids(self, client_logged_in, faker, version):
        """Test bulk delete succeeds and reports missing IDs."""
        source1 = SourceFactory()
        source2 = SourceFactory()
        non_existent_id = generate_invalid_id(faker)
        delete_request = {"ids": [non_existent_id, source1.id, source2.id]}
        url = reverse(f"{version}:source-bulk-delete")
        response = client_logged_in.post(url, data=delete_request)
        assert response.ok
        response_json = response.json()
        assert set(response_json["deleted"]) == set([source1.id, source2.id])
        assert response_json["missing"] == [non_existent_id]
        assert response_json["skipped"] == []
        assert not Source.objects.filter(pk__in=[source1.id, source2.id]).exists()

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_bulk_delete_ignores_errors(self, client_logged_in, version):
        """Test bulk delete succeeds and reports skipped IDs."""
        source = SourceFactory()
        source_in_use = SourceFactory()
        scan1 = ScanFactory(sources=[source_in_use])
        scan2 = ScanFactory(sources=[source_in_use])
        delete_request = {"ids": [source_in_use.id, source.id]}
        url = reverse(f"{version}:source-bulk-delete")
        response = client_logged_in.post(url, data=delete_request)
        assert response.ok
        response_json = response.json()
        assert response_json["deleted"] == [source.id]
        assert response_json["missing"] == []
        assert len(response_json["skipped"]) == 1
        assert response_json["skipped"][0]["source"] == source_in_use.id
        assert set(response_json["skipped"][0]["scans"]) == set([scan1.id, scan2.id])
        assert not Source.objects.filter(pk=source.id).exists()
        assert Source.objects.filter(pk=source_in_use.id).exists()

    @pytest.mark.parametrize("version", ["v1", "v2"])
    def test_bulk_delete_all(self, client_logged_in, celery_worker, version):
        """Test bulk delete succeeds with magic "all" token."""
        source1 = SourceFactory()
        source1_in_use = SourceFactory()
        scan1 = ScanFactory(sources=[source1_in_use])
        assert scan1.sources.filter(pk=source1_in_use.id).exists()

        source2 = SourceFactory()
        source2_in_use = SourceFactory()
        scan2 = ScanFactory(sources=[source2_in_use])
        scan2job = ScanJobFactory(scan=scan2)
        scan2job.sources.add(source2_in_use)
        scan2task = ScanTaskFactory(job=scan2job, source=source2_in_use)
        assert scan2.sources.filter(pk=source2_in_use.id).exists()
        assert scan2task.source == source2_in_use

        # Note that scan3task is directly related to source3_in_use
        # but its ScanJob has no Scan. This means it should not prevent
        # source3_in_use from being deleted.
        source3_in_use = SourceFactory()
        scan3task = ScanTaskFactory(source=source3_in_use)
        assert scan3task.source == source3_in_use
        assert scan3task.job.scan is None

        delete_request = {"ids": ALL_IDS_MAGIC_STRING}
        url = reverse(f"{version}:source-bulk-delete")
        response = client_logged_in.post(url, data=delete_request)
        assert response.ok
        response_json = response.json()
        assert set(response_json["deleted"]) == {
            source1.id,
            source2.id,
            source3_in_use.id,
        }
        assert response_json["missing"] == []

        # Note that lists like "skipped" may not be sorted.
        expected_skipped = sorted(
            [
                {"source": source1_in_use.id, "scans": [scan1.id]},
                {"source": source2_in_use.id, "scans": [scan2.id]},
            ],
            key=lambda skipped: skipped["source"],
        )
        actual_skipped = sorted(
            response_json["skipped"], key=lambda skipped: skipped["source"]
        )
        assert expected_skipped == actual_skipped

        assert not Source.objects.exclude(
            pk__in=[source1_in_use.id, source2_in_use.id]
        ).exists()
        assert Source.objects.filter(
            pk__in=[source1_in_use.id, source2_in_use.id]
        ).exists()

        # Note that even though ScanJobs and ScanTasks may reference a Source,
        # at the time of this writing, we simply break the relationship and
        # orphan those objects. This *may* result in jobs and tasks that are
        # otherwise unreachable and unusable by the end user. See also discussion:
        # https://redhat-internal.slack.com/archives/C02QSNF1UKE/p1710439062155129?thread_ts=1710430876.780099&cid=C02QSNF1UKE  # noqa
        scan3task.refresh_from_db()
        assert scan3task.source is None
