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
"""Util for re-loading partial scan jobs and their results."""

from api.models import ScanJob, ScanJobResults
from scanner.discovery import DiscoveryScanner
from scanner.host import HostScanner


def create_scanner_for_job(scanjob, fact_endpoint):
    """Given a job, read partial results and create new scanner.

    :param scanjob: Results for this scanjob will be retreived
    :returns: the scanner object to be run
    """
    scan_results = ScanJobResults.objects.filter(
        scan_job=scanjob.id).first()

    scanner = None
    if scanjob.scan_type == ScanJob.DISCOVERY:
        scanner = DiscoveryScanner(scanjob, scan_results=scan_results)
    else:
        scanner = HostScanner(
            scanjob, fact_endpoint, scan_results=scan_results)
    return scanner
