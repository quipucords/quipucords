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

"""Flow server version to clients."""

from quipucords.environment import server_version


class ServerVersionMiddle:
    """Middleware class to flow server version to clients."""

    # pylint: disable=too-few-public-methods
    def __init__(self, get_response):
        """Initialize middleware class."""
        self.get_response = get_response

    def __call__(self, request):
        """Add server version header to response."""
        response = self.get_response(request)
        response["X-Server-Version"] = server_version()
        return response
