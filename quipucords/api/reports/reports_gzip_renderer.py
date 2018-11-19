#
# Copyright (c) 2018 Red Hat, Inc.
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

from api.common.util import create_tar_buffer
from api.deployments_report.util import create_deployments_csv
from api.details_report.util import create_details_csv

from rest_framework import renderers

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

NETWORK_DETECTION_KEY = 'detection-network'
VCENTER_DETECTION_KEY = 'detection-vcenter'
SATELLITE_DETECTION_KEY = 'detection-satellite'
SOURCES_KEY = 'sources'


class ReportsGzipRenderer(renderers.BaseRenderer):
    """Class to render reports as tar.gz."""

    # pylint: disable=too-few-public-methods
    media_type = 'application/gzip'
    format = 'tar.gz'
    render_style = 'binary'

    def render(self, reports_dict, media_type=None, renderer_context=None):
        """Render all reports as gzip."""
        # pylint: disable=arguments-differ,unused-argument,too-many-locals
        # pylint: disable=too-many-branches,too-many-statements
        # pylint: disable=too-many-return-statements
        report_list = []
        if not bool(reports_dict):
            return None

        report_id = reports_dict.get('report_id')
        if report_id is None:
            return None

        # details
        details_json = reports_dict.get('details_json')
        if details_json is None:
            return None
        report_list.append(details_json)

        details_csv = create_details_csv(details_json)
        if details_csv is None:
            return None
        report_type = details_json.get('report_type')
        if report_type is None:
            report_type = 'details'
        details_csv_tuple = (details_csv, report_id, report_type)
        report_list.append(details_csv_tuple)

        # deployments
        deployments_json = reports_dict.get('deployments_json')
        if deployments_json is None:
            return None
        report_list.append(deployments_json)

        deployments_csv = create_deployments_csv(deployments_json)
        if deployments_csv is None:
            return None
        report_type = deployments_json.get('report_type')
        if report_type is None:
            report_type = 'deployments'
        deployments_csv_tuple = (deployments_csv, report_id, report_type)
        report_list.append(deployments_csv_tuple)

        tar_buffer = create_tar_buffer(report_list)
        if tar_buffer is None:
            return None
        tar_buffer = tar_buffer.getvalue()
        with open('test.tar.gz', 'wb') as out_file:
            out_file.write(tar_buffer)
        return tar_buffer
