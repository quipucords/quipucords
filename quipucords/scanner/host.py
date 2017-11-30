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
"""Scanner used for host inspection."""
import os
import logging
import requests
from ansible.errors import AnsibleError
from ansible.executor.task_queue_manager import TaskQueueManager
from api.models import ScanJob, Credential
from scanner.discovery import DiscoveryScanner
from scanner.callback import ResultCallback
from scanner.utils import (construct_scan_inventory, write_inventory,
                           run_playbook,
                           _construct_error_msg)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
PLAYBOOK_PATH = os.path.abspath(os.path.normpath(
    os.path.join(os.path.curdir, 'playbooks', 'host_scan_playbook.yaml')))


class ScannerException(Exception):
    """Exception for issues detected during scans."""

    def __init__(self, message=''):
        """Exception for issues detected during scans.

        :param message: An error message describing the problem encountered
        during scan.
        """
        self.message = 'Scan failed.  Error: {}'.format(message)
        super().__init__(self.message)


class HostScanner(DiscoveryScanner):
    """Scan target systems to collect facts.

    Attempts connections to a network profile using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip). Runs a host scan on the set of systems that are
    reachable. Collects the associated facts for the scanned systems
    """

    def __init__(self, scanjob, fact_endpoint, scan_results=None):
        """Create host scanner."""
        DiscoveryScanner.__init__(self, scanjob, scan_results)
        self.fact_endpoint = fact_endpoint

    # pylint: disable=too-many-locals
    def host_scan(self):
        """Execute the host scan with the initialized network profile.

        :returns: An array of dictionaries of facts
        """
        facts = []
        roles = ['check_dependencies', 'connection',
                 'cpu', 'date', 'dmi', 'etc_release',
                 'virt', 'virt_what', 'host_done']
        playbook = {'name': 'scan systems for product fingerprint facts',
                    'hosts': 'all',
                    'gather_facts': False,
                    'strategy': 'free',
                    'roles': roles}
        connection_port = self.network_profile['ssh_port']

        connected, failed, completed = self.obtain_discovery_data()
        forks = self.scanjob.max_concurrency

        num_completed = len(completed)
        num_remaining = len(connected)
        num_total = num_remaining + num_completed
        num_failed = len(failed)

        if num_total == 0:
            msg = 'Inventory provided no reachable hosts.'
            raise ScannerException(msg)

        if self.scan_restart:
            logger.info('Host scan restarted for %s.',
                        self.scanjob)
        else:
            logger.info('Host scan started for %s.',
                        self.scanjob)
        log_msg = '%d total connected, %d completed, %d'\
            ' remaining, and make %d failed hosts'
        logger.info(log_msg,
                    num_total, num_completed, num_remaining, num_failed)

        # Save counts
        self.scanjob.systems_count = len(connected)
        self.scanjob.systems_scanned = 0
        self.scanjob.failed_scans = 0
        self.scanjob.save()

        forks = self.scanjob.max_concurrency
        group_names, inventory = construct_scan_inventory(
            connected, connection_port, forks)
        inventory_file = write_inventory(inventory)

        error_msg = ''
        for group_name in group_names:
            callback = ResultCallback(scanjob=self.scanjob,
                                      scan_results=self.scan_results)
            playbook = {'name': 'scan systems for product fingerprint facts',
                        'hosts': group_name,
                        'gather_facts': False,
                        'roles': roles}
            result = run_playbook(
                inventory_file, callback, playbook, forks=forks)

            if result != TaskQueueManager.RUN_OK:
                new_error_msg = _construct_error_msg(result)
                logger.error(new_error_msg)
                error_msg += '{}\n'.format(new_error_msg)

        if error_msg != '':
            raise AnsibleError(error_msg)

        # Process all results that were save to db
        for scan_result in self.scan_results.results.all():
            if scan_result.row == 'success' or scan_result.row == 'failed':
                continue
            fact = {}
            for column in scan_result.columns.all():
                if column.value is None or column.value == '':
                    continue
                fact[column.key] = column.value
            facts.append(fact)

        logger.debug('Facts obtained from host scan: %s', facts)
        logger.info('Host scan completed for %s.', self.scanjob)
        return facts

    def obtain_discovery_data(self):
        """Obtain discover scan data.  Either via new scan or paused scan.

        :returns: List of connected and failed.
        """
        if self.scan_restart:
            result_map = {}
            for result in self.scan_results.results.all():
                result_map[result.row] = result

            connected = self.create_host_list(result_map['success'], True)
            del result_map['success']
            failed = self.create_host_list(result_map['failed'], False)
            del result_map['failed']

            # Remove scanned systems from the set
            completed = set(result_map.keys())
            connected = [
                host for host in connected if host[0] not in completed]

            return connected, failed, completed

        connected, failed = self.discovery()
        completed = []
        self._store_discovery_success(
            connected, failed, mark_complete=False)
        return connected, failed, completed

    # pylint: disable=no-self-use
    def create_host_list(self, scan_result, lookup_creds):
        """Convert a scan_result into a host list.

        :param scan_result: The scan_result to inspect
        :param lookup_creds: Whether creds should be included in result
        :returns: List of connected and failed.  Optionally include creds.
        """
        ip_list = []
        for column in scan_result.columns.all():
            credential = None
            if lookup_creds and column.value is not None:
                host_cred = Credential.objects.get(name=column.value)
                credential = {'name': host_cred.name,
                              'username': host_cred.username,
                              'password': host_cred.password,
                              'sudo_password': host_cred.sudo_password,
                              'ssh_keyfile': host_cred.ssh_keyfile,
                              'ssh_passphrase': host_cred.ssh_passphrase}
                ip_list.append((column.key, credential))
            else:
                ip_list.append(column.key)
        return ip_list

    def send_facts(self, facts):
        """Send collected host scan facts to fact endpoint.

        :param facts: The array of fact dictionaries
        :returns: Identifer for the sent facts
        """
        payload = {'facts': facts}
        response = requests.post(self.fact_endpoint, json=payload)
        data = response.json()
        msg = 'Failed to obtain fact_collection_id when reporting facts.'
        if response.status_code != 201 or data['id'] is None:
            raise ScannerException('{} Error: {}'.format(msg, data))
        return data['id']

    def _store_host_scan_success(self, fact_collection_id):
        self.scan_results.fact_collection_id = fact_collection_id
        self.scan_results.save()
        self.scanjob.status = ScanJob.COMPLETED
        self.scanjob.save()
        return self.scan_results

    def run(self):
        """Trigger thread execution."""
        facts = []
        self.scanjob.status = ScanJob.RUNNING
        self.scanjob.save()

        try:
            # Execute scan
            facts = self.host_scan()

            # Send facts to fact endpoint
            fact_size = len(facts)
            if facts is None or fact_size == 0:
                msg = 'Fact set is empty.  '\
                    'No results will be reported to fact endpoint.'
                raise ScannerException(msg)

            fact_collection_id = self.send_facts(facts)

            # Save the fact collection id to scanjob
            self.scanjob.fact_collection_id = fact_collection_id
            self.scanjob.save()

            self._store_host_scan_success(fact_collection_id)
            logger.info('Host scan successfully completed for job: %s.',
                        self.scanjob)
        except AnsibleError as ansible_error:
            logger.error(ansible_error)
            self._store_error(ansible_error)
        except AssertionError as assertion_error:
            logger.error(assertion_error)
            self._store_error(assertion_error)
        except ScannerException as scan_error:
            logger.error(scan_error)
            self._store_error(scan_error)
        return facts
