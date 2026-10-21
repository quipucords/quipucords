"""tar.gz renderer for Lightspeed reports."""

import logging

from rest_framework import renderers, status
from rest_framework.renderers import JSONRenderer

from api.common.common_report import create_tar_buffer, encode_content

logger = logging.getLogger(__name__)


class LightspeedGzipRenderer(renderers.BaseRenderer):
    """Class to render Lightspeed reports as tar.gz."""

    media_type = "application/gzip"
    format = "tar.gz"
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render all reports as gzip."""
        # DRF uses this renderer for all responses when Accept: application/gzip,
        # including framework-generated errors (401, 429, etc.) that bypass the view.
        # For those error responses we must render as JSON explicitly; DRF will not
        # fall back to JSONRenderer on its own.
        if (
            renderer_context
            and renderer_context.get("response")
            and renderer_context["response"].status_code >= status.HTTP_400_BAD_REQUEST
        ):
            renderer_context["response"]["Content-Type"] = "application/json"
            return JSONRenderer().render(
                data,
                accepted_media_type="application/json",
                renderer_context=renderer_context,
            )
        lightspeed_dict = data
        if not lightspeed_dict:
            return None
        lightspeed_encoded = {
            file_name: encode_content(json_data, "json")
            for file_name, json_data in lightspeed_dict.items()
        }
        return create_tar_buffer(lightspeed_encoded)
