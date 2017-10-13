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
"""Scanner used for host inspection"""
import os
import logging
import uuid
import requests
from ansible.errors import AnsibleError
from ansible.executor.task_queue_manager import TaskQueueManager
from api.networkprofile_serializer import NetworkProfileSerializer
from api.scanjob_model import ScanJob
from api.scanresults_model import ScanJobResults, Results, ResultKeyValue
from scanner.discovery import DiscoveryScanner
from scanner.callback import ResultCallback
from scanner.utils import (construct_scan_inventory, write_inventory,
                           run_playbook, _construct_error)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
PLAYBOOK_PATH = os.path.abspath(os.path.normpath(
    os.path.join(os.path.curdir, 'playbooks', 'host_scan_playbook.yaml')))


class HostScanner(DiscoveryScanner):
    """Attempts connections to a network profile using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip). Runs a host scan on the set of systems that are
    reachable. Collects the associated facts for the scanned systems
    """

    def __init__(self, scanjob, network_profile, fact_endpoint):
        DiscoveryScanner.__init__(self, scanjob, network_profile)
        self.scanjob = scanjob
        serializer = NetworkProfileSerializer(network_profile)
        self.network_profile = serializer.data
        self.fact_endpoint = fact_endpoint

    # pylint: disable=too-many-locals
    def host_scan(self):
        """Executes the host scan with the initialized network profile

        :returns: An array of dictionaries of facts
        """
        facts = []
        playbook = {'name': 'scan systems for product fingerprint facts',
                    'hosts': 'all',
                    'gather_facts': False,
                    'roles': ['etc_release']}
        connection_port = self.network_profile['ssh_port']

        logger.info('Host scan started for %s.', self.scanjob)
        connected, failed = self.discovery()  # pylint: disable=unused-variable

        inventory = construct_scan_inventory(connected, connection_port)
        inventory_file = write_inventory(inventory)
        callback = ResultCallback()
        result = run_playbook(inventory_file, callback, playbook)

        if result != TaskQueueManager.RUN_OK:
            raise _construct_error(result)

        dict_facts = callback.ansible_facts
        for host, sys_fact in dict_facts.items():
            sys_fact['connection_port'] = connection_port
            sys_fact['connection_host'] = host
            sys_fact['connection_uuid'] = str(uuid.uuid4())
            facts.append(sys_fact)

        logger.debug('Facts obtained from host scan: %s', facts)
        logger.info('Host scan completed for %s.', self.scanjob)
        return facts

    def send_facts(self, facts):
        """Send collected host scan facts to fact endpoint and get
        associated id.

        :param facts: The array of fact dictionaries
        :returns: Identifer for the sent facts
        """
        payload = {'facts': facts}
        response = requests.post(self.fact_endpoint, json=payload)
        data = response.json()
        msg = 'Failed to obtain fact_collection_id when reporting facts.'
        assert 'id' in data, msg
        return data['id']

    def _store_host_scan_success(self, facts, fact_collection_id):
        scan_results = ScanJobResults(scan_job=self.scanjob,
                                      fact_collection_id=fact_collection_id)
        scan_results.save()
        for fact in facts:
            row = Results()
            row.save()
            for key, value in fact.items():
                stored_fact = ResultKeyValue(key=key, value=value)
                stored_fact.save()
                row.columns.add(stored_fact)
            row.save()
            scan_results.results.add(row)
        scan_results.save()
        self.scanjob.status = ScanJob.COMPLETED
        self.scanjob.save()
        return scan_results

    def run(self):
        """Method via thread for triggering execution"""
        facts = []
        self.scanjob.status = ScanJob.RUNNING
        self.scanjob.save()

        try:
            # Execute scan
            facts = self.host_scan()

            # Send facts to fact endpoint
            fact_collection_id = self.send_facts(facts)
            self._store_host_scan_success(facts, fact_collection_id)
        except AnsibleError as ansible_error:
            logger.error(ansible_error)
            self._store_error(ansible_error)
        except AssertionError as assertion_error:
            logger.error(assertion_error)
            self._store_error(assertion_error)

        return facts
