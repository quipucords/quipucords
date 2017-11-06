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

"""Signal manager to handle scan triggering."""

import django.dispatch
from api.models import ScanJob
from scanner.discovery import DiscoveryScanner
from scanner.host import HostScanner


def handle_scan(sender, instance, fact_endpoint, **kwargs):
    """Handle incoming scan.

    :param sender: Class that was saved
    :param instance: ScanJob that was saved
    :param fact_endpoint: The API endpoint to send collect fact to
    :param kwargs: Other args
    :returns: None
    """
    # pylint: disable=unused-argument
    if kwargs.get('created', False):
        # nothing need for an existing scan.
        return

    if instance.scan_type == ScanJob.DISCOVERY:
        scan = DiscoveryScanner(instance)
        scan.start()
    else:
        scan = HostScanner(instance, fact_endpoint)
        scan.start()


# pylint: disable=C0103
start_scan = django.dispatch.Signal(providing_args=['instance',
                                                    'fact_endpoint'])
start_scan.connect(handle_scan)
