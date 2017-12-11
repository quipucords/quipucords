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
"""Admin module for Django server application."""

from django.contrib import admin
from api.models import (FactCollection, SystemFingerprint, Credential,
                        Source, ScanJob, ConnectionResults, InspectionResults)

admin.site.register(FactCollection)
admin.site.register(Credential)
admin.site.register(Source)
admin.site.register(SystemFingerprint)
admin.site.register(ScanJob)
admin.site.register(ConnectionResults)
admin.site.register(InspectionResults)
