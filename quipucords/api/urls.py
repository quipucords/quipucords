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
from rest_framework_expiring_authtoken import views
from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns
from api.views import (CredentialViewSet,
                       FactViewSet,
                       SourceViewSet,
                       ScanViewSet,
                       ScanJobViewSet,
                       ReportListView,
                       UserViewSet)


ROUTER = SimpleRouter()

ROUTER.register(r'credentials',
                CredentialViewSet,
                base_name='cred')
ROUTER.register(r'facts',
                FactViewSet,
                base_name='facts')
ROUTER.register(r'sources',
                SourceViewSet,
                base_name='source')
ROUTER.register(r'scans',
                ScanViewSet,
                base_name='scan')
ROUTER.register(r'jobs',
                ScanJobViewSet,
                base_name='scanjob')
ROUTER.register(r'users',
                UserViewSet,
                base_name='users')

# pylint: disable=invalid-name
urlpatterns = [
    url(r'^reports/$', ReportListView.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)

urlpatterns += [
    url(r'^token/', views.obtain_expiring_auth_token)
]

urlpatterns += ROUTER.urls
