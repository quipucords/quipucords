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

from api.models import (
    Credential,
    DetailsReport,
    JobConnectionResult,
    JobInspectionResult,
    Scan,
    ScanJob,
    ServerInformation,
    Source,
    SystemFingerprint,
)

from django.contrib import admin

admin.site.register(ServerInformation)
admin.site.register(DetailsReport)
admin.site.register(Credential)
admin.site.register(Source)
admin.site.register(SystemFingerprint)
admin.site.register(Scan)
admin.site.register(ScanJob)
admin.site.register(JobConnectionResult)
admin.site.register(JobInspectionResult)
