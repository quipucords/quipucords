"""tar.gz renderer for insights reports."""

import logging

from rest_framework import renderers

from api.common.common_report import create_tar_buffer, encode_content

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class InsightsGzipRenderer(renderers.BaseRenderer):
    """Class to render insights reports as tar.gz."""

    # pylint: disable=too-few-public-methods
    media_type = "application/gzip"
    format = "tar.gz"
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render all reports as gzip."""
        insights_dict = data
        if not insights_dict:
            return None
        insights_encoded = {
            file_name: encode_content(json_data, "json")
            for file_name, json_data in insights_dict.items()
        }
        return create_tar_buffer(insights_encoded)
