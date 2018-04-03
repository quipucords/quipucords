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

"""View for server status."""

from api import API_VERSION

from quipucords.environment import (commit,
                                    modules,
                                    platform_info,
                                    python_version)

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def status(request):
    """Provide the server status information."""
    server_info = {
        'api_version': API_VERSION,
    }
    commit_info = commit()
    if commit_info:
        server_info['build'] = commit_info
    server_info['server_address'] = request.META.get('HTTP_HOST', 'localhost')
    server_info['platform'] = platform_info()
    server_info['python'] = python_version()
    server_info['modules'] = modules()
    return Response(server_info)
