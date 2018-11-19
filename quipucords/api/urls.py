#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Describes the urls and patterns for the API application."""

from api.views import (CredentialViewSet,
                       DetailsReportsViewSet,
                       ScanJobViewSet,
                       ScanViewSet,
                       SourceViewSet,
                       UserViewSet,
                       async_merge_reports,
                       deployments,
                       details,
                       jobs,
                       reports,
                       status,
                       sync_merge_reports)

from django.urls import path

from rest_framework.routers import SimpleRouter

from rest_framework_expiring_authtoken import views

ROUTER = SimpleRouter()

ROUTER.register(r'credentials',
                CredentialViewSet,
                base_name='cred')
ROUTER.register(r'reports',
                DetailsReportsViewSet,
                base_name='reports')
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
    path('reports/<int:pk>/', reports),
    path('reports/<int:pk>/details/', details),
    path('reports/<int:pk>/deployments/', deployments),
    path('reports/merge/', sync_merge_reports),
    path('reports/merge/jobs/', async_merge_reports),
    path('reports/merge/jobs/<int:pk>/', async_merge_reports),
    path('scans/<int:pk>/jobs/', jobs),
]

urlpatterns += [
    path('token/', views.obtain_expiring_auth_token)
]

urlpatterns += [
    path('status/', status, name='server-status'),
]

urlpatterns += ROUTER.urls
