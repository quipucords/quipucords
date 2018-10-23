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

import io
import json
import logging
import tarfile

from api.models import (DetailsReport)

from rest_framework import renderers

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class DetailsJsonGzipRenderer(renderers.BaseRenderer):
    """Class to render Details report as tar.gz containging a json file."""

    # pylint: disable=too-few-public-methods
    media_type = 'application/json+gzip'
    format = 'tar.gz'
    render_style = 'binary'

    def render(self, report_dict, media_type=None, renderer_context=None):
        """Render deployment report as json gzip."""
        # pylint: disable=arguments-differ,unused-argument,too-many-locals
        # pylint: disable=too-many-branches,too-many-statements

        if not bool(report_dict):
            return None

        report_id = report_dict.get('report_id')
        if report_id is None:
            return None

        details_report = DetailsReport.objects.filter(
            report_id=report_id).first()
        if details_report is None:
            return None

        json_buffer = io.BytesIO(json.dumps(report_dict).encode('utf-8'))
        tar_buffer = io.BytesIO()
        with tarfile.TarFile(fileobj=tar_buffer,
                             mode='w',
                             debug=3) as tar_file:
            info = tarfile.TarInfo(name='report.json')
            info.size = len(json_buffer.getvalue())
            tar_file.addfile(tarinfo=info, fileobj=json_buffer)
        tar_buffer.seek(0)
        return tar_buffer
