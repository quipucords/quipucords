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

from rest_framework import renderers

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ReportJsonGzipRenderer(renderers.BaseRenderer):
    """Class to render reports as tar.gz containing a json file."""

    # pylint: disable=too-few-public-methods
    media_type = 'application/json+gzip'
    format = 'tar.gz'
    render_style = 'binary'

    def render(self, report_dict, media_type=None, renderer_context=None):
        """Render report as json gzip."""
        # pylint: disable=arguments-differ,unused-argument,too-many-locals
        # pylint: disable=too-many-branches,too-many-statements

        if not bool(report_dict):
            return None

        report_id = report_dict.get('report_id')
        if report_id is None:
            return None

        tar_buffer = create_tar_buffer([report_dict])
        return tar_buffer
