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
"""Scanner used for host connection discovery"""
import logging
from threading import Thread
from api.networkprofile_serializer import NetworkProfileSerializer
from api.hostcredential_model import HostCredential
from api.hostcredential_serializer import HostCredentialSerializer
from api.scanresults_model import ScanJobResults, Results, ResultKeyValue
from scanner.utils import connect


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class DiscoveryScanner(Thread):
    """Attempts connections to a network profile using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    def __init__(self, scanjob, network_profile):
        Thread.__init__(self)
        self.scanjob = scanjob
        serializer = NetworkProfileSerializer(network_profile)
        self.network_profile = serializer.data

    # pylint: disable=too-many-locals
    def run(self):
        """Executes the discovery scan with the initialized network profile
        """
        result = {}
        connected = []
        remaining_hosts = self.network_profile['hosts']
        credentials = self.network_profile['credentials']
        connection_port = self.network_profile['ssh_port']

        logger.info('Discovery scan started for %s.', self.scanjob)

        for cred_id in credentials:
            cred_obj = HostCredential.objects.get(pk=cred_id)
            hc_serializer = HostCredentialSerializer(cred_obj)
            cred = hc_serializer.data
            connected, remaining_hosts = connect(remaining_hosts, cred,
                                                 connection_port)
            if remaining_hosts == []:
                break

        success_row = Results(row='success')
        success_row.save()
        for success in connected:
            result[success[0]] = success[1]
            rkv1 = ResultKeyValue(key=success[0], value=success[1]['name'])
            rkv1.save()
            success_row.columns.add(rkv1)
        success_row.save()

        failed_row = Results(row='failed')
        failed_row.save()
        for failed in remaining_hosts:
            result[failed] = None
            rkv1 = ResultKeyValue(key=failed, value=None)
            rkv1.save()
            failed_row.columns.add(rkv1)
        failed_row.save()

        scan_results = ScanJobResults(scan_job=self.scanjob)
        scan_results.save()
        scan_results.results.add(success_row)
        scan_results.results.add(failed_row)
        scan_results.save()

        logger.info('Discovery scan completed for %s.', self.scanjob)

        return result
