"""report.pagination module."""

from rest_framework.response import Response

from ..common.pagination import StandardResultsSetPagination


class ReportPagination(StandardResultsSetPagination):
    """
    Custom paginator exclusive to report views.

    It was made to be used in tandem with class based views that inherit from
    ReportViewMixin.
    """

    def __init__(self, *, report_platform_id, report_version, report_type):
        super().__init__()
        self._report_metadata = {
            "report_platform_id": report_platform_id,
            "report_version": report_version,
            "report_type": report_type,
        }

    def get_paginated_response(self, data) -> Response:
        """Get paginated response."""
        response: Response = super().get_paginated_response(data)
        response.data.update(self._report_metadata)
        # pop and add results again just to change dict order
        # (IMO having paging + report info grouped together is better for readability)
        response.data["results"] = response.data.pop("results")
        return response
