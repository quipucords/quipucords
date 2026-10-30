"""tar.gz renderer for Lightspeed reports."""

import logging

from rest_framework import renderers

from api.common.common_report import create_tar_buffer, encode_content

logger = logging.getLogger(__name__)


class LightspeedGzipRenderer(renderers.BaseRenderer):
    """Class to render Lightspeed reports as tar.gz."""

    media_type = "application/gzip"
    format = "tar.gz"
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render all reports as gzip."""
        lightspeed_dict = data
        if not lightspeed_dict:
            return None
        lightspeed_encoded = {
            file_name: encode_content(json_data, "json")
            for file_name, json_data in lightspeed_dict.items()
        }
        return create_tar_buffer(lightspeed_encoded)
