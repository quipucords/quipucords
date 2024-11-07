"""Test the RawFactReportView API."""

from unittest.mock import ANY

import pytest
from django.urls import reverse
from rest_framework import status

from api.report.view import RawFactsReportView
from constants import DataSources
from tests.factories import ReportFactory

# exclude OpenShift as a source as it messes with the expected result per source count
FIXED_LENGTH_DATASOURCES = list(set(DataSources.values) - {DataSources.OPENSHIFT})


@pytest.mark.django_db
class TestRawFactReportView:
    """Test RawFactReportView."""

    def test_get_raw_facts_report_success(self, client_logged_in, faker):
        """Test successful retrieval of raw facts report."""
        # Create a report with raw facts
        report = ReportFactory(
            generate_raw_facts=True,
            generate_raw_facts__source_types=[
                faker.random_element(FIXED_LENGTH_DATASOURCES)
            ],
            generate_raw_facts__qty_per_source=3,
        )

        url = reverse("v2:report-raw", args=(report.id,))
        response = client_logged_in.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify pagination structure
        assert "count" in data
        assert "next" in data
        assert "previous" in data
        assert "results" in data

        # Verify report metadata from pagination
        assert data["report_platform_id"] == str(report.report_platform_id)
        assert data["report_version"] == report.report_version
        assert data["report_type"] == "raw_facts"

        # Verify results structure
        results = data["results"]
        assert len(results) > 0

        for result in results:
            assert "raw_facts" in result
            assert "metadata" in result
            assert isinstance(result["raw_facts"], dict)
            assert isinstance(result["metadata"], dict)

            # Verify metadata structure
            metadata = result["metadata"]
            assert "source_name" in metadata
            assert "source_type" in metadata
            assert "server_id" in metadata

    def test_get_raw_facts_report_not_found(self, client_logged_in):
        """Test getting raw facts for non-existent report."""
        non_existent_id = 999999
        url = reverse("v2:report-raw", args=(non_existent_id,))
        response = client_logged_in.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_raw_facts_report_empty_report(self, client_logged_in):
        """Test getting raw facts for report with no inspect results."""
        report = ReportFactory()  # No raw facts generated

        url = reverse("v2:report-raw", args=(report.id,))
        response = client_logged_in.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have pagination structure but empty results
        assert data["count"] == 0
        assert data["results"] == []
        assert data["report_platform_id"] == str(report.report_platform_id)

    def test_pagination_functionality(self, client_logged_in, faker):
        """Test pagination with large dataset."""
        # Create report with many inspect results
        report = ReportFactory(
            generate_raw_facts=True,
            generate_raw_facts__source_types=[
                faker.random_element(FIXED_LENGTH_DATASOURCES)
            ],
            generate_raw_facts__qty_per_source=25,
        )

        url = reverse("v2:report-raw", args=(report.id,))

        # Get first page
        response = client_logged_in.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["count"] == 25
        assert len(data["results"]) == 25

        # Test page size parameter to force pagination
        response = client_logged_in.get(url, {"page_size": 20})
        assert response.status_code == status.HTTP_200_OK
        page1 = response.json()

        assert len(page1["results"]) == 20  # First page should have 20 elements
        assert page1["next"] is not None  # Should have next page

        # Test second page
        # response = client_logged_in.get(url, {"page": 2, "page_size": 20})
        response = client_logged_in.get(page1["next"])
        assert response.status_code == status.HTTP_200_OK
        page2 = response.json()

        assert (
            len(page2["results"]) == 5
        )  # Second page should have remaining 5 elements
        assert page2["previous"] is not None  # Should have previous page
        assert page2["next"] is None  # Should be the last page

    def test_compare_raw_facts_with_details_report_content(self, client_logged_in):
        """Test that raw facts data matches details report data structure."""
        # Create test data using sources format (same as details report)
        test_sources = [
            {
                "server_id": "test-server-1",
                "source_name": "test-source-network",
                "source_type": DataSources.NETWORK,
                "report_version": "1.0.0",
                "facts": [
                    {"hostname": "server1.example.com", "ip_address": "192.168.1.10"},
                    {"hostname": "server2.example.com", "ip_address": "192.168.1.11"},
                ],
            },
            {
                "server_id": "test-server-2",
                "source_name": "test-source-satellite",
                "source_type": DataSources.SATELLITE,
                "report_version": "1.0.0",
                "facts": [
                    {"name": "rhel-host-1", "version": "8.4"},
                    {"name": "rhel-host-2", "version": "8.5"},
                ],
            },
        ]

        report = ReportFactory(sources=test_sources)

        # Get raw facts
        raw_facts_url = reverse("v2:report-raw", args=(report.id,))
        raw_facts_response = client_logged_in.get(raw_facts_url)
        assert raw_facts_response.status_code == status.HTTP_200_OK
        raw_facts_data = raw_facts_response.json()

        # Get details report for comparison
        details_url = reverse("v1:reports-details", args=(report.id,))
        details_response = client_logged_in.get(details_url)
        assert details_response.status_code == status.HTTP_200_OK
        details_data = details_response.json()

        # Verify basic report metadata matches
        assert (
            raw_facts_data["report_platform_id"] == details_data["report_platform_id"]
        )
        assert raw_facts_data["report_version"] == details_data["report_version"]

        # Convert raw facts to comparable format
        raw_facts_by_source = {}
        for result in raw_facts_data["results"]:
            metadata = result["metadata"]
            source_key = (
                metadata["server_id"],
                metadata["source_name"],
                metadata["source_type"],
            )
            if source_key not in raw_facts_by_source:
                raw_facts_by_source[source_key] = []
            raw_facts_by_source[source_key].append(result["raw_facts"])

        # Convert details report sources to comparable format
        details_by_source = {}
        for source in details_data["sources"]:
            source_key = (
                source["server_id"],
                source["source_name"],
                source["source_type"],
            )
            details_by_source[source_key] = source["facts"]

        # Compare the data structures
        assert len(raw_facts_by_source) == len(details_by_source)

        for source_key, raw_facts_list in raw_facts_by_source.items():
            assert source_key in details_by_source

            details_facts_list = details_by_source[source_key]

            # Should have same number of facts
            assert len(raw_facts_list) == len(details_facts_list)

            # Convert lists to sets of frozensets for comparison (order independent)
            raw_facts_set = {frozenset(fact.items()) for fact in raw_facts_list}
            details_facts_set = {frozenset(fact.items()) for fact in details_facts_list}

            # The actual fact content should be identical
            assert raw_facts_set == details_facts_set

    def test_raw_facts_serializer_structure(self, client_logged_in):
        """Test that raw facts follow expected serializer structure."""
        report = ReportFactory(
            generate_raw_facts=True,
            generate_raw_facts__source_types=[DataSources.NETWORK],
            generate_raw_facts__qty_per_source=1,
        )

        url = reverse("v2:report-raw", args=(report.id,))
        response = client_logged_in.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        result = data["results"][0]

        # Verify required fields from InspectResultSerializer
        assert "raw_facts" in result
        assert "metadata" in result

        # Verify metadata contains InspectGroup fields (excluding excluded ones)
        metadata = result["metadata"]
        required_metadata_fields = [
            "source_name",
            "source_type",
            "server_id",
            "server_version",
        ]
        for field in required_metadata_fields:
            assert field in metadata

        # Verify excluded fields are not present
        excluded_fields = ["id", "created_at", "updated_at", "tasks"]
        for field in excluded_fields:
            assert field not in metadata

        # Verify raw_facts is a dictionary
        assert isinstance(result["raw_facts"], dict)
        assert len(result["raw_facts"]) > 0

    def test_report_mixin_functionality(self, client_logged_in, faker):
        """
        Test that ReportViewMixin is working correctly.

        This makes sure the that report info like id and version are available alongside
        pagination data.
        """
        report = ReportFactory(
            generate_raw_facts=True,
            generate_raw_facts__source_types=[
                faker.random_element(FIXED_LENGTH_DATASOURCES)
            ],
            generate_raw_facts__qty_per_source=2,
        )

        url = reverse("v2:report-raw", args=(report.id,))
        response = client_logged_in.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data == {
            "count": 2,
            "next": None,
            "previous": None,
            "report_platform_id": str(report.report_platform_id),
            "report_type": "raw_facts",
            "report_version": report.report_version,
            "results": [ANY, ANY],
        }

        # Verify the metadata is at the end (after results)
        keys = list(data.keys())
        assert keys[-1] == "results"  # results should be last per ReportPagination

    def test_queryset_performance(self, django_assert_num_queries, faker):
        """Test RawFactsReportView queryset performance."""
        data_sources = faker.random_elements(
            FIXED_LENGTH_DATASOURCES,
            unique=True,
            length=2,
        )

        # Create test data with multiple InspectResults and related RawFacts
        report = ReportFactory(
            generate_raw_facts=True,
            generate_raw_facts__source_types=data_sources,
            generate_raw_facts__qty_per_source=5,  # Creates 10 InspectResults total
        )

        # Filter the queryset to only include results for our report
        # This mimics what the view does with get_queryset()
        view_queryset = RawFactsReportView.queryset.filter(
            inspect_group__reports__id=report.id
        )

        # The optimized queryset should execute efficiently:
        # 1. Main query to get InspectResults with annotation
        # 2. Prefetch query for inspect_group data
        # Total: 2 queries regardless of number of results
        with django_assert_num_queries(2):
            results = list(view_queryset)

        with django_assert_num_queries(0):
            # Access the prefetched data to ensure it doesn't trigger additional queries
            for result in results:
                # Access raw_facts (from annotation)
                assert isinstance(result.raw_facts, dict)
                assert len(result.raw_facts) > 0
                assert result.inspect_group.source_type in data_sources

                # Access inspect_group (from prefetch_related)
                inspect_group = result.inspect_group
                assert inspect_group.source_type is not None
                assert inspect_group.source_name is not None
                assert inspect_group.server_id is not None

        # Verify we got the expected number of results
        assert len(results) == 10  # 2 sources * 5 facts each
