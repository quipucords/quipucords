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
from api.models import ScanJob
from scanner.discovery import DiscoveryScanner
from scanner.callback import ResultCallback
from scanner.utils import (construct_scan_inventory, write_inventory,
                           run_playbook, _construct_error)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
PLAYBOOK_PATH = os.path.abspath(os.path.normpath(
    os.path.join(os.path.curdir, 'playbooks', 'host_scan_playbook.yaml')))


class HostScanner(DiscoveryScanner):
    """Scan target systems to collect facts.

    Attempts connections to a network profile using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip). Runs a host scan on the set of systems that are
    reachable. Collects the associated facts for the scanned systems
    """

    def __init__(self, scanjob, fact_endpoint):
        """Create host scanner."""
        DiscoveryScanner.__init__(self, scanjob)
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

        logger.info('Host scan started for %s.', self.scanjob)
        connected, failed = self.discovery()  # pylint: disable=unused-variable
        self._store_discovery_success(connected, failed, mark_complete=False)
        forks = self.scanjob.max_concurrency

        # Save counts
        self.scanjob.systems_count = len(connected)
        self.scanjob.systems_scanned = 0
        self.scanjob.save()

        forks = self.scanjob.max_concurrency
        group_names, inventory = construct_scan_inventory(
            connected, connection_port, forks)
        inventory_file = write_inventory(inventory)
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
                raise _construct_error(result)

            dict_facts = callback.ansible_facts
            # pylint: disable=unused-variable
            for host, sys_fact in dict_facts.items():
                new_sys_fact = {}
                for fact_key, fact_value in sys_fact.items():
                    if fact_value:
                        new_sys_fact[fact_key] = fact_value
                facts.append(new_sys_fact)

        logger.debug('Facts obtained from host scan: %s', facts)
        logger.info('Host scan completed for %s.', self.scanjob)
        return facts

    def send_facts(self, facts):
        """Send collected host scan facts to fact endpoint.

        :param facts: The array of fact dictionaries
        :returns: Identifer for the sent facts
        """
        payload = {'facts': facts}
        response = requests.post(self.fact_endpoint, json=payload)
        data = response.json()
        msg = 'Failed to obtain fact_collection_id when reporting facts.'
        if response.status_code != 201:
            logger.error('Could not create facts. Errors: %s', data)
            assert 'id' in data, msg
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
            fact_collection_id = self.send_facts(facts)

            # Save the fact collection id to scanjob
            self.scanjob.fact_collection_id = fact_collection_id
            self.scanjob.save()

            self._store_host_scan_success(fact_collection_id)
        except AnsibleError as ansible_error:
            logger.error(ansible_error)
            self._store_error(ansible_error)
        except AssertionError as assertion_error:
            logger.error(assertion_error)
            self._store_error(assertion_error)

        return facts
