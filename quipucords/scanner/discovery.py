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
"""Scanner used for host connection discovery."""
import logging
from multiprocessing import Process
from ansible.errors import AnsibleError
from api.serializers import SourceSerializer, CredentialSerializer
from api.models import (Credential, ScanJob, ScanJobResults,
                        Results, ResultKeyValue)
from scanner.utils import connect


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class DiscoveryScanner(Process):
    """Discovery system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    def __init__(self, scanjob, scan_results=None):
        """Create discovery scanner."""
        Process.__init__(self)
        self.scanjob = scanjob
        self.identifier = scanjob.id
        source = scanjob.source
        serializer = SourceSerializer(source)
        self.source = serializer.data
        if scan_results is None:
            self.scan_results = ScanJobResults(scan_job=self.scanjob)
            self.scan_restart = False
        else:
            self.scan_results = scan_results
            self.scan_restart = True

    def _store_discovery_success(self, connected, failed_hosts,
                                 mark_complete=True):
        result = {}
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
        for failed in failed_hosts:
            result[failed] = None
            rkv1 = ResultKeyValue(key=failed, value=None)
            rkv1.save()
            failed_row.columns.add(rkv1)
        failed_row.save()

        self.scan_results.save()
        self.scan_results.results.add(success_row)
        self.scan_results.results.add(failed_row)
        self.scan_results.save()

        if mark_complete:
            self.scanjob.status = ScanJob.COMPLETED
            self.scanjob.save()

        return result

    def _store_error(self, ansible_error):
        self.scanjob.status = ScanJob.FAILED
        self.scanjob.save()
        self.scan_results.save()
        error_row = Results(row='error')
        error_row.save()
        rkv1 = ResultKeyValue(key='message', value=ansible_error.message)
        rkv1.save()
        error_row.columns.add(rkv1)
        self.scan_results.results.add(error_row)
        self.scan_results.save()

    def run(self):
        """Trigger thread execution."""
        result = {}
        self.scanjob.status = ScanJob.RUNNING
        self.scanjob.save()
        try:
            connected, failed_hosts = self.discovery()
            result = self._store_discovery_success(connected, failed_hosts)
        except AnsibleError as ansible_error:
            logger.error('Discovery scan failed for %s. %s', self.scanjob,
                         ansible_error)
            self._store_error(ansible_error)

        return result

    # pylint: disable=too-many-locals
    def discovery(self):
        """Execute the discovery scan with the initialized source.

        :returns: list of connected hosts credential tuples and
                  list of host that failed connection
        """
        connected = []
        remaining = self.source['hosts']
        credentials = self.source['credentials']
        connection_port = self.source['ssh_port']

        logger.info('Discovery scan started for %s.', self.scanjob)

        forks = self.scanjob.max_concurrency
        for cred_id in credentials:
            cred_obj = Credential.objects.get(pk=cred_id)
            hc_serializer = CredentialSerializer(cred_obj)
            cred = hc_serializer.data
            connected, remaining = connect(remaining, cred, connection_port,
                                           forks=forks)

            # Update the scan counts
            if self.scanjob.scan_type == ScanJob.DISCOVERY:
                if self.scanjob.systems_count is None:
                    self.scanjob.systems_count = len(
                        connected) + len(remaining)
                    self.scanjob.systems_scanned = 0
                self.scanjob.systems_scanned += len(connected)
                self.scanjob.save()

            if remaining == []:
                break

        logger.info('Discovery scan completed for %s.', self.scanjob)
        logger.info('Successfully connected to %d systems.', len(connected))
        if len(remaining) > 0:  # pylint: disable=len-as-condition
            logger.warning('Failed to connect to %d systems.', len(remaining))
            logger.debug('Failed systems: %s', remaining)

        return connected, remaining
