"""Test the ReportPagination class.

This module provides tests for the ReportPagination class which extends
DRF's PageNumberPagination to include report metadata in paginated responses.
"""

from api.report.pagination import ReportPagination


class TestReportPagination:
    """Test ReportPagination class."""

    def test_pagination_schema_includes_report_metadata(self):
        """Test that ReportPagination schema includes report metadata fields."""
        # Create a pagination instance
        pagination = ReportPagination()

        # Create a sample schema (what would be passed in)
        sample_schema = {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
        }

        # Get the paginated response schema
        schema = pagination.get_paginated_response_schema(sample_schema)

        assert schema == {
            "properties": {
                "count": {"example": 123, "type": "integer"},
                "next": {
                    "example": "http://api.example.org/accounts/?page=4",
                    "format": "uri",
                    "nullable": True,
                    "type": "string",
                },
                "previous": {
                    "example": "http://api.example.org/accounts/?page=2",
                    "format": "uri",
                    "nullable": True,
                    "type": "string",
                },
                "report_platform_id": {
                    "description": "The global identifier of the report",
                    "format": "uuid",
                    "type": "string",
                },
                "report_type": {
                    "description": "The type of the report",
                    "type": "string",
                },
                "report_version": {
                    "description": "The version of the report",
                    "type": "string",
                },
                "results": sample_schema,
            },
            "required": [
                "count",
                "results",
                "report_platform_id",
                "report_version",
                "report_type",
            ],
            "type": "object",
        }
