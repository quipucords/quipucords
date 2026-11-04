"""tar.gz renderer for insights reports."""

import logging

from rest_framework import renderers, status

from api.common.common_report import create_tar_buffer, encode_content

logger = logging.getLogger(__name__)


class InsightsGzipRenderer(renderers.BaseRenderer):
    """Class to render insights reports as tar.gz."""

    media_type = "application/gzip"
    format = "tar.gz"
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render all reports as gzip."""
        # Return None for error responses to let JSON renderer handle it.
        if (
            renderer_context
            and renderer_context.get("response")
            and renderer_context["response"].status_code >= status.HTTP_400_BAD_REQUEST
        ):
            return None
        insights_dict = data
        if not insights_dict:
            return None
        insights_encoded = {
            file_name: encode_content(json_data, "json")
            for file_name, json_data in insights_dict.items()
        }
        return create_tar_buffer(insights_encoded)
