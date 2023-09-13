"""tar.gz renderer for reports."""

import hashlib
import logging

from rest_framework import renderers

from api import messages
from api.common.common_report import create_filename, create_tar_buffer, encode_content
from api.deployments_report.util import create_deployments_csv
from api.details_report.util import create_details_csv

logger = logging.getLogger(__name__)


class ReportsGzipRenderer(renderers.BaseRenderer):
    """Class to render all reports as tar.gz."""

    media_type = "application/gzip"
    format = "tar.gz"
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render all reports as gzip."""
        reports_dict = data
        if not bool(reports_dict):
            return None
        report_id = reports_dict.get("report_id")
        # Collect Json Data
        details_json = reports_dict.get("details_json")
        deployments_json = reports_dict.get("deployments_json")
        if any(value is None for value in [report_id, details_json, deployments_json]):
            return None

        # Collect CSV Data
        details_csv = create_details_csv(details_json)
        deployments_csv = create_deployments_csv(deployments_json)
        if any(value is None for value in [details_csv, deployments_csv]):
            return None

        # create the file names
        details_json_name = create_filename("details", "json", report_id)
        deployments_json_name = create_filename("deployments", "json", report_id)
        details_csv_name = create_filename("details", "csv", report_id)
        deployments_csv_name = create_filename("deployments", "csv", report_id)
        sha256sum_name = create_filename("SHA256SUM", None, report_id)

        # map the file names to the file data
        files_data = {
            details_json_name: encode_content(details_json, "json"),
            deployments_json_name: encode_content(deployments_json, "json"),
            details_csv_name: encode_content(details_csv, "csv"),
            deployments_csv_name: encode_content(deployments_csv, "csv"),
        }

        # generate hashes
        sha256sum_content = ""
        for full_file_name, content in files_data.items():
            file_name = full_file_name.rsplit("/", 1)[1]
            sha256 = hashlib.sha256(content).hexdigest()
            sha256sum_content += f"{sha256}  {file_name}\n"
        files_data[sha256sum_name] = encode_content(sha256sum_content, "plaintext")

        tar_buffer = create_tar_buffer(files_data)
        if tar_buffer is None:
            logger.error(messages.REPORTS_TAR_ERROR)
            return None
        return tar_buffer
