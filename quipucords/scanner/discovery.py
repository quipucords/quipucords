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
from api.models import (Credential, ScanJob, ConnectionResults,
                        ConnectionResult, SystemConnectionResult)
from scanner.utils import connect


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class DiscoveryScanner(Process):
    """Discovery system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    def __init__(self, scanjob, conn_results=None):
        """Create discovery scanner."""
        Process.__init__(self)
        self.scanjob = scanjob
        self.identifier = scanjob.id
        self.source = scanjob.source
        if conn_results is None:
            self.conn_results = ConnectionResults(scan_job=self.scanjob)
            self.scan_restart = False
        else:
            self.conn_results = conn_results
            self.scan_restart = True

    def _store_discovery_success(self, connected, failed_hosts,
                                 mark_complete=True):
        result = {}
        conn_result = ConnectionResult(source=self.source)
        conn_result.save()

        for success in connected:
            result[success[0]] = success[1]
            cred = Credential.objects.get(pk=success[1]['id'])
            sys_result = SystemConnectionResult(
                name=success[0], status=SystemConnectionResult.SUCCESS,
                credential=cred)
            sys_result.save()
            conn_result.systems.add(sys_result)

        for failed in failed_hosts:
            result[failed] = None
            sys_result = SystemConnectionResult(
                name=failed, status=SystemConnectionResult.FAILED)
            sys_result.save()
            conn_result.systems.add(sys_result)

        conn_result.save()
        self.conn_results.save()
        self.conn_results.results.add(conn_result)
        self.conn_results.save()

        if mark_complete:
            self.scanjob.status = ScanJob.COMPLETED
            self.scanjob.save()

        return result

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
            self.scanjob.status = ScanJob.FAILED
            self.scanjob.save()

        return result

    # pylint: disable=too-many-locals
    def discovery(self):
        """Execute the discovery scan with the initialized source.

        :returns: list of connected hosts credential tuples and
                  list of host that failed connection
        """
        connected = []
        serializer = SourceSerializer(self.source)
        source = serializer.data
        remaining = source['hosts']
        credentials = source['credentials']
        connection_port = source['ssh_port']

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
