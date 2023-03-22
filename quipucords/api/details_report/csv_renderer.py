"""CSV renderer for reports."""

from rest_framework import renderers

from api.details_report.util import create_details_csv


class DetailsCSVRenderer(renderers.BaseRenderer):
    """Class to render report as CSV."""

    media_type = "text/csv"
    format = "csv"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render report as CSV."""
        return create_details_csv(data, renderer_context.get("request"))
