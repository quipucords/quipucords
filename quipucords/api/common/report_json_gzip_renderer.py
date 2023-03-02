"""tar.gz renderer for reports."""

import logging
import time

from rest_framework import renderers

from api.common.common_report import create_filename, create_tar_buffer, encode_content

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ReportJsonGzipRenderer(renderers.BaseRenderer):
    """Class to render reports as tar.gz containing a json file."""

    # pylint: disable=too-few-public-methods
    media_type = "application/json+gzip"
    format = "tar.gz"
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render report as json gzip."""
        report_dict = data
        if not bool(report_dict):
            return None

        report_id = report_dict.get("report_id")
        report_type = report_dict.get("report_type")
        if report_id is None:
            return None
        if report_type is None:
            file_name = f"{time.strftime('%Y%m%d%H%M%S')}.json"
        else:
            file_name = create_filename(report_type, "json", report_id)
        report_encoded = encode_content(report_dict, "json")
        file_data = {file_name: report_encoded}
        tar_buffer = create_tar_buffer(file_data)
        return tar_buffer
