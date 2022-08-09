#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""tar.gz renderer for insights reports."""

import logging

from api.common.common_report import create_tar_buffer

from rest_framework import renderers

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

        return create_tar_buffer(insights_dict)
