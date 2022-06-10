#
# Copyright (c) 2017-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Callback object for capturing ansible task execution."""

import json
import logging

from ansible_runner.exceptions import AnsibleRunnerException
from django.conf import settings
from django.db import transaction

import log_messages
from api.models import RawFact, SystemInspectionResult
from scanner.network.processing import process
from scanner.network.utils import STOP_STATES, raw_facts_template

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

STARTED_PROCESSING_ROLE = 'internal_host_started_processing_role'
HOST_DONE = 'host_done'
INTERNAL_ = 'internal_'
TIMEOUT_RC = 124  # 'timeout's return code when it times out.
UNKNOWN = 'unknown_host'


class InspectResultCallback():
    """A sample callback plugin used for performing an action.

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """

    # pylint: disable=protected-access
    def __init__(self, scan_task, manager_interrupt):
        """Create result callback."""
        self.scan_task = scan_task
        self.source = scan_task.source
        self._ansible_facts = {}
        self.last_role = None
        self.stopped = False
        self.interrupt = manager_interrupt

    def process_task_facts(self, task_facts, host):
        """Collect, process, and save task facts."""
        host_facts = {}
        for key, value in task_facts.items():
            if key == HOST_DONE:
                self._finalize_host(host, SystemInspectionResult.SUCCESS)
            else:
                processed_value = process.process(
                    self.scan_task, self._ansible_facts.get(host, {}),
                    key, value, host)
                host_facts[key] = processed_value
        if bool(host_facts) and host != UNKNOWN:
            if host in self._ansible_facts:
                self._ansible_facts[host].update(host_facts)
            else:
                self._ansible_facts[host] = host_facts

    def task_on_ok(self, event_dict):
        """Print a json representation of the event_data on ok."""
        event_data = event_dict.get('event_data')
        host = event_data.get('host', UNKNOWN)
        result = event_data.get('res')
        task_action = event_data.get('task_action')
        task = event_data.get('task')
        # Print Role started for each host
        if task_action == 'set_fact' and task == STARTED_PROCESSING_ROLE:
            log_message = 'PROCESSING %s - ANSIBLE ROLE %s' % (
                host, self.last_role)
            self.scan_task.log_message(log_message)
        task_facts = result.get('ansible_facts')
        if task_facts:
            self.process_task_facts(task_facts, host)

    def task_on_failed(self, event_dict):
        """Print a json representation of the event_data on failed."""
        event_data = event_dict.get('event_data')
        host = event_data.get('host', UNKNOWN)
        result = event_data.get('res')
        if result.get('rc') == TIMEOUT_RC:
            logger.warning('Task %s timed out', event_data['task'])

        # Only log an error when ignore errors is false
        if event_dict.get('ignore_errors', False):
            err_reason = result.get('msg', event_data)
            err_msg = 'FAILING HOST %s - Unexpected ansible error:  %s'
            self.scan_task.log_message(err_msg % (host, err_reason),
                                       log_level=logging.ERROR)
        task_facts = result.get('ansible_facts')
        if task_facts:
            self.process_task_facts(task_facts, host)

    # NOTE: that @transaction.atomic functions will only modify the database if
    # a response without errors is produced. These are called after all details
    # for a report is complete for a host. Writing results need to be atomic so
    # that host won't be marked as complete unless we actually save its results

    @transaction.atomic
    def finalize_failed_hosts(self):
        """
        Finalize failed host.

        This method labels the hosts as failed to keep the
        system counter for logging correct.
        """
        # Label all host as failed so that the system counter for
        # logging is correct.
        host_list = list(self._ansible_facts.keys())
        for host in host_list:
            self._finalize_host(host, SystemInspectionResult.FAILED)

    @transaction.atomic
    def _finalize_host(self, host, host_status):
        """Save facts collected and update the scan counts."""
        results = raw_facts_template()
        results.update(self._ansible_facts.pop(host, {}))

        if settings.QPC_EXCLUDE_INTERNAL_FACTS:
            # remove internal facts before saving result
            results = {fact_key: fact_value
                       for fact_key, fact_value in results.items(
                       ) if not fact_key.startswith(INTERNAL_)}
        self.scan_task.log_message('host scan complete for %s.  '
                                   'Status: %s. Facts %s' %
                                   (host, host_status, results),
                                   log_level=logging.DEBUG)

        # Update scan counts
        if self.scan_task is not None:
            if host_status == SystemInspectionResult.SUCCESS:
                self.scan_task.increment_stats(
                    host, increment_sys_scanned=True)
            elif host_status == SystemInspectionResult.UNREACHABLE:
                self.scan_task.increment_stats(
                    host, increment_sys_unreachable=True)
            else:
                self.scan_task.increment_stats(
                    host, increment_sys_failed=True)

        sys_result = SystemInspectionResult(
            name=host,
            status=host_status,
            source=self.scan_task.source,
            task_inspection_result=self.scan_task.inspection_result)
        sys_result.save()

        # Generate facts for host
        for result_key, result_value in results.items():
            if result_value == process.NO_DATA:
                result_value = None

            # Convert all values to JSON.  Noop for str, int
            final_value = json.dumps(result_value)
            stored_fact = RawFact(name=result_key,
                                  value=final_value,
                                  system_inspection_result=sys_result)
            stored_fact.save()

    @transaction.atomic
    def task_on_unreachable(self, event_dict):
        """Print a json representation of the event_data on unreachable."""
        event_data = event_dict.get('event_data')
        host = event_data.get('host', UNKNOWN)
        result_message = event_data.get(
            'msg',
            'No information given on unreachable warning.')
        message = 'UNREACHABLE %s. %s' % (host, result_message)
        self.scan_task.log_message(message, log_level=logging.ERROR)
        self._finalize_host(host, SystemInspectionResult.UNREACHABLE)

    def event_callback(self, event_dict=None):
        """Control the event callback for Ansible Runner."""
        try:
            okay = ['runner_on_ok', 'runner_item_on_ok']
            failed = ['runner_on_failed', 'runner_item_on_failed']
            unreachable = ['runner_on_unreachable']
            runner_ignore = ['runner_on_skipped',
                             'runner_item_on_skipped']
            event = event_dict.get('event')
            event_data = event_dict.get('event_data')

            ignore_states = ['runner_on_start']
            if event in ignore_states:
                return

            if event_dict:
                # Check if it is a task event
                if 'runner' in event:
                    if event in okay:
                        self.task_on_ok(event_dict)
                    elif event in failed:
                        self.task_on_failed(event_dict)
                    elif event in unreachable:
                        self.task_on_unreachable(event_dict)
                    else:
                        if event not in runner_ignore:
                            self.scan_task.log_message(
                                log_messages.TASK_UNEXPECTED_FAILURE % (
                                    'event_callback', event,
                                    event_dict),
                                log_level=logging.ERROR)
                # Save last role for task logging later
                if event == 'playbook_on_task_start':
                    if event_data:
                        event_role = event_data.get('role')
                        if event_role != self.last_role:
                            self.last_role = event_role
        except Exception as err_msg:
            raise AnsibleRunnerException(err_msg)

    def cancel_callback(self):
        """Control the cancel callback for runner."""
        if self.stopped:
            return True
        for stop_type, stop_value in STOP_STATES.items():
            if self.interrupt.value == stop_value:
                self.scan_task.log_message(
                    log_messages.NETWORK_CALLBACK_ACK_STOP % (
                        'INSPECT',
                        stop_type),
                    log_level=logging.INFO)
                self.stopped = True
                return True
        return False
