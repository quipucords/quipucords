#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Describes the urls and patterns for the API application"""

from rest_framework.routers import SimpleRouter
from api import views


ROUTER = SimpleRouter()

ROUTER.register(r'credentials/hosts',
                views.HostCredentialViewSet,
                base_name='hostcred')
ROUTER.register(r'profiles/networks',
                views.NetworkProfileViewSet,
                base_name='networkprofile')

# pylint: disable=invalid-name
urlpatterns = ROUTER.urls
