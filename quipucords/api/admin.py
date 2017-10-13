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
"""Admin module for Django server application"""

from django.contrib import admin
from api.fact_model import FactCollection
from api.hostcredential_model import HostCredential
from api.networkprofile_model import NetworkProfile
from api.report_model import SystemFingerprint
from api.scanjob_model import ScanJob
from api.scanresults_model import ScanJobResults

admin.site.register(FactCollection)
admin.site.register(HostCredential)
admin.site.register(NetworkProfile)
admin.site.register(SystemFingerprint)
admin.site.register(ScanJob)
admin.site.register(ScanJobResults)
