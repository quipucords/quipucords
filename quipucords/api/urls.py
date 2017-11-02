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
"""Describes the urls and patterns for the API application."""

from django.conf.urls import url
from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns
from api.views import (HostCredentialViewSet, FactViewSet,
                       NetworkProfileViewSet, ScanJobViewSet, ReportListView)


ROUTER = SimpleRouter()

ROUTER.register(r'credentials/hosts',
                HostCredentialViewSet,
                base_name='hostcred')
ROUTER.register(r'facts',
                FactViewSet,
                base_name='facts')
ROUTER.register(r'profiles/networks',
                NetworkProfileViewSet,
                base_name='networkprofile')
ROUTER.register(r'scans',
                ScanJobViewSet,
                base_name='scanjob')

urlpatterns = [
    url(r'^reports/$', ReportListView.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)

# pylint: disable=invalid-name
urlpatterns += ROUTER.urls
