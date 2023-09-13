"""CSV renderer for reports."""

from rest_framework import renderers

from api.deployments_report.util import create_deployments_csv


class DeploymentCSVRenderer(renderers.BaseRenderer):
    """Class to render report as CSV."""

    media_type = "text/csv"
    format = "csv"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render report as CSV."""
        return create_deployments_csv(data)
