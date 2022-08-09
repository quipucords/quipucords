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
"""CSV renderer for reports."""

from api.details_report.util import create_details_csv

from rest_framework import renderers


class DetailsCSVRenderer(renderers.BaseRenderer):
    """Class to render report as CSV."""

    # pylint: disable=too-few-public-methods
    media_type = "text/csv"
    format = "csv"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Render report as CSV."""
        return create_details_csv(data, renderer_context.get("request"))
