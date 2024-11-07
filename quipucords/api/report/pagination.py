"""report.pagination module."""

from rest_framework.response import Response

from ..common.pagination import StandardResultsSetPagination


class ReportPagination(StandardResultsSetPagination):
    """
    Custom paginator exclusive to report views.

    It was made to be used in tandem with class based views that inherit from
    ReportViewMixin.
    """

    def __init__(self):
        super().__init__()
        self._report_metadata = {}

    def add_report_metadata(self, *, report_platform_id, report_version, report_type):
        """
        Add metadata information to the report.

        Args:
            report_platform_id (str): The global identifier of the report.
            report_version (str): The version of the report.
            report_type (str): The type the report.

        """
        self._report_metadata.update(
            report_platform_id=report_platform_id,
            report_version=report_version,
            report_type=report_type,
        )

    def get_paginated_response(self, data) -> Response:
        """Get paginated response."""
        if not self._report_metadata:
            raise ValueError(
                f"{self.__class__.__name__} not properly initialized. Run "
                "'add_report_metadata' name before calling this method."
            )
        response = super().get_paginated_response(data)
        # response.data is always a dict and has a "results" key; ignore type checker
        response.data.update(self._report_metadata)  # type: ignore
        # Move "results" to the end for readability
        response.data["results"] = response.data.pop("results")  # type: ignore
        return response

    def get_paginated_response_schema(self, schema):
        """Get paginated response schema with added report metadata fields."""
        # Get the base pagination schema from the parent class
        paginated_schema = super().get_paginated_response_schema(schema)

        # Add the report metadata fields to the schema properties
        paginated_schema["properties"].update(
            {
                "report_platform_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "The global identifier of the report",
                },
                "report_version": {
                    "type": "string",
                    "description": "The version of the report",
                },
                "report_type": {
                    "type": "string",
                    "description": "The type of the report",
                },
            }
        )

        # Add the new fields to the required list
        paginated_schema["required"].extend(
            ["report_platform_id", "report_version", "report_type"]
        )

        return paginated_schema
