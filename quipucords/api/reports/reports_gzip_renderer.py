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

import logging

import api.messages as messages
from api.common.common_report import (create_filename, create_tar_buffer)
from api.deployments_report.util import create_deployments_csv
from api.details_report.util import create_details_csv

from rest_framework import renderers

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ReportsGzipRenderer(renderers.BaseRenderer):
    """Class to render all reports as tar.gz."""

    # pylint: disable=too-few-public-methods
    media_type = 'application/gzip'
    format = 'tar.gz'
    render_style = 'binary'

    def render(self, reports_dict, media_type=None, renderer_context=None):
        """Render all reports as gzip."""
        # pylint: disable=arguments-differ,unused-argument,too-many-locals
        # pylint: disable=too-many-branches,too-many-statements
        if not bool(reports_dict):
            return None

        files_data = dict()

        report_id = reports_dict.get('report_id')
        # Collect Json Data
        details_json = reports_dict.get('details_json')
        deployments_json = reports_dict.get('deployments_json')
        insights_json = reports_dict.get('insights_json')
        if any(value is None for value in [report_id,
                                           details_json,
                                           deployments_json]):
            return None
        details_name = create_filename('details', 'json', report_id)
        files_data[details_name] = details_json
        deployments_name = create_filename('deployments', 'json', report_id)
        files_data[deployments_name] = deployments_json
        if insights_json:
            insights_name = create_filename('insights', 'json', report_id)
            files_data[insights_name] = insights_json
        # Collect CSV Data
        details_csv = create_details_csv(details_json)
        deployments_csv = create_deployments_csv(deployments_json)
        if any(value is None for value in [details_csv, deployments_json]):
            return None
        details_csv_name = create_filename('details', 'csv', report_id)
        files_data[details_csv_name] = details_csv
        deployments_csv_name = create_filename('deployments', 'csv', report_id)
        files_data[deployments_csv_name] = deployments_csv
        tar_buffer = create_tar_buffer(files_data)
        if tar_buffer is None:
            logger.error(messages.REPORTS_TAR_ERROR)
            return None
        return tar_buffer
