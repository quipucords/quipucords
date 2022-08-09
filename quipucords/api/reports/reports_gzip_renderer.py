#
# Copyright (c) 2018-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""tar.gz renderer for reports."""

import hashlib
import json
import logging
import os
import tempfile

from rest_framework import renderers

import api.messages as messages
from api.common.common_report import create_filename, create_tar_buffer
from api.deployments_report.util import create_deployments_csv
from api.details_report.util import create_details_csv

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def create_tempfile(report_data, suffix):
    """Create a temporary file with the report data."""
    temporary_file = tempfile.NamedTemporaryFile(delete=False)
    temp_rep = open(temporary_file.name, "wb")
    if suffix == "json":
        myrepcontents = json.dumps(report_data).encode("utf-8")
    elif suffix == "csv":
        myrepcontents = str(report_data).encode("utf-8")
    temp_rep.write(myrepcontents)
    temp_rep.close()
    return temporary_file.name


def create_hash(report_data, suffix):
    """Create a temporary file, generate a hash, and delete the file.

    :param: report_data: <dict> or <str> the report data in csv or json format
    :param: suffix: <str> the file suffix (json or csv)
    :returns: sha256 hash.
    """
    temp_file = create_tempfile(report_data, suffix)  # create a temp file
    block_size = 65536  # The size of each read from the file
    # Create the hash object
    file_hash = hashlib.sha256()
    with open(temp_file, "rb") as temp_rep:  # Open the file to read it's bytes
        # Read from the file. Take in the amount declared above
        file_block = temp_rep.read(block_size)
        while len(file_block) > 0:  # While there is still data being read
            file_hash.update(file_block)  # Update the hash
            # Read the next block from the file
            file_block = temp_rep.read(block_size)
        temp_rep.close()
    os.remove(temp_file)  # remove the temp file
    return file_hash.hexdigest()  # Get the hexadecimal digest of the hash


class ReportsGzipRenderer(renderers.BaseRenderer):
    """Class to render all reports as tar.gz."""

    # pylint: disable=too-few-public-methods
    media_type = "application/gzip"
    format = "tar.gz"
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render all reports as gzip."""
        # pylint: disable=too-many-locals
        request = renderer_context.get("request")
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
        details_csv = create_details_csv(details_json, request)
        deployments_csv = create_deployments_csv(deployments_json, request)
        if any(value is None for value in [details_csv, deployments_csv]):
            return None

        # grab hashes
        details_json_hash = create_hash(details_json, "json")
        deployments_json_hash = create_hash(deployments_json, "json")
        details_csv_hash = create_hash(details_csv, "csv")
        deployments_csv_hash = create_hash(deployments_csv, "csv")

        # create the file names
        details_json_name = create_filename("details", "json", report_id)
        deployments_json_name = create_filename("deployments", "json", report_id)
        details_csv_name = create_filename("details", "csv", report_id)
        deployments_csv_name = create_filename("deployments", "csv", report_id)
        sha256sum_name = create_filename("SHA256SUM", None, report_id)

        # map the file names to the file data
        files_data = {
            details_json_name: details_json,
            deployments_json_name: deployments_json,
            details_csv_name: details_csv,
            deployments_csv_name: deployments_csv,
            sha256sum_name: details_json_hash
            + "  details.json\n"
            + deployments_json_hash
            + "  deployments.json\n"
            + details_csv_hash
            + "  details.csv\n"
            + deployments_csv_hash
            + "  deployments.csv",
        }

        tar_buffer = create_tar_buffer(files_data)
        if tar_buffer is None:
            logger.error(messages.REPORTS_TAR_ERROR)
            return None
        return tar_buffer
