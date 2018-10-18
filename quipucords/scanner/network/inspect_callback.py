#
# Copyright (c) 2017-2018 Red Hat, Inc.
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
import traceback

from ansible.plugins.callback import CallbackBase

from api.models import (RawFact,
                        SystemInspectionResult)

from django.db import transaction

from quipucords import settings

from scanner import scan_data_log
from scanner.network.processing import process

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

ANSIBLE_FACTS = 'ansible_facts'
STARTED_PROCESSING_ROLE = 'internal_host_started_processing_role'
FAILED = 'failed'
HOST = 'host'
HOST_DONE = 'host_done'
INTERNAL_ = 'internal_'
KEY = 'key'
NO_KEY = 'no_key'
RC = 'rc'
RESULT = 'result'

TIMEOUT_RC = 124  # 'timeout's return code when it times out.


def _construct_result(result):
    """Construct result object."""
    # pylint: disable=protected-access
    host = result._host
    if host is not None:
        hostname = host.name
    else:
        hostname = 'unknown host'

    if result._task is not None and \
            result._task.register is not None:
        key = result._task.register
    else:
        key = NO_KEY
    return {HOST: hostname, RESULT: result._result, KEY: key}


def normalize_result(result):
    """Normalize the representation of an Ansible result.

    We see Ansible results in three forms:
      1) raw task with register variable whose name starts with 'internal_'
      2) raw task with register variable whose name does not start
         with 'internal_'
      3) set_facts task with member called 'ansible_facts'

    :param result: Ansible result dictionary
    :returns: [] for case 1, and a list of key, value tuples for
        cases 2 and 3.
    """
    # pylint: disable=protected-access
    if result._result is not None and isinstance(result._result, dict):
        # pylint: disable=no-else-return
        if ANSIBLE_FACTS in result._result:
            return [(key, value)
                    for key, value in result._result[ANSIBLE_FACTS].items()]
        elif isinstance(result._task.register, str):
            return [(result._task.register, result._result)]

    return []


class InspectResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action.

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """

    # pylint: disable=protected-access
    def __init__(self, scan_task, display=None):
        """Create result callback."""
        super().__init__(display=display)
        self.scan_task = scan_task
        self.source = scan_task.source
        self.results = []
        self._ansible_facts = {}

    # Ansible considers tasks failed when their return code is
    # nonzero, even if we set ignore_errors=True. We want to be able
    # to process those task results, so we need to handle failed
    # results the same way we treat ok ones.
    def v2_runner_on_ok(self, result):
        """Print a json representation of the result."""
        try:
            self.handle_result(result)
        except Exception as error:
            self.scan_task.log_message(
                'UNEXPECTED FAILURE in v2_runner_on_ok.'
                '  Error: %s\nAnsible result: %s' % (
                    error, result._result),
                log_level=logging.ERROR)
            traceback.print_exc()
            raise error

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Print a json representation of the result."""
        # pylint: disable=protected-access
        try:
            with_items = result._result.get('results') is not None
            if not with_items and result._result.get('msg') is not None:
                result_obj = _construct_result(result)
                if result_obj.get('key') != 'internal_user_has_sudo_cmd':
                    host = result._host
                    if host is not None:
                        hostname = host.name
                    else:
                        hostname = 'unknown host'

                    self.scan_task.log_message(
                        'FAILING HOST %s - Unexpected ansible error:  %s' % (
                            hostname, result._result),
                        log_level=logging.ERROR)
            self.handle_result(result)
        except Exception as error:
            self.scan_task.log_message(
                'UNEXPECTED FAILURE in v2_runner_on_failed.'
                '  Error: %s\nAnsible result: %s' % (
                    error, result._result),
                log_level=logging.ERROR)
            traceback.print_exc()
            raise error

    def handle_result(self, result):
        """Handle an incoming result object."""
        scan_data_log.safe_log_ansible_result(result, self.scan_task)
        # pylint: disable=protected-access
        result_obj = _construct_result(result)
        self.results.append(result_obj)
        logger.debug('%s', result_obj)

        # 'timeout' returns 124 on timeouts
        if result_obj[RESULT].get(FAILED) and \
           result_obj[RESULT].get(RC) == TIMEOUT_RC:
            logger.warning('Task %s timed out', result_obj[KEY])

        host = result_obj[HOST]
        results_to_store = normalize_result(result)
        host_facts = {}
        if result._task_fields.get('action') == 'set_fact' and \
                result.task_name == 'internal_host_started_processing_role':
            role_name = result._result.get(
                ANSIBLE_FACTS).get(STARTED_PROCESSING_ROLE)
            log_message = 'PROCESSING %s - ANSIBLE ROLE %s' % (host, role_name)
            self.scan_task.log_message(log_message)
        for key, value in results_to_store:
            if key == HOST_DONE:
                self._finalize_host(host, SystemInspectionResult.SUCCESS)
            else:
                processed_value = process.process(
                    self.scan_task, self._ansible_facts.get(host, {}),
                    key, value, host)
                host_facts[key] = processed_value

        if bool(host_facts):
            if host in self._ansible_facts:
                self._ansible_facts[host].update(host_facts)
            else:
                self._ansible_facts[host] = host_facts

    # Called after all details report is complete for host. Writing
    # results needs to be atomic so that the host won't be marked
    # as complete unless we actually save its results.
    @transaction.atomic
    def finalize_failed_hosts(self):
        """Finalize failed host."""
        host_list = list(self._ansible_facts.keys())
        for host in host_list:
            self._finalize_host(host, SystemInspectionResult.FAILED)

    # Called after all details report is complete for host. Writing
    # results needs to be atomic so that the host won't be marked
    # as complete unless we actually save its results.
    @transaction.atomic
    def _finalize_host(self, host, host_status):
        results = self._ansible_facts.pop(host, {})

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
            name=host, status=host_status, source=self.scan_task.source)
        sys_result.save()

        self.scan_task.inspection_result.systems.add(sys_result)
        self.scan_task.inspection_result.save()

        # Generate facts for host
        for result_key, result_value in results.items():
            if result_value == process.NO_DATA:
                continue

            # Convert all values to JSON.  Noop for str, int
            final_value = json.dumps(result_value)
            stored_fact = RawFact(name=result_key,
                                  value=final_value)
            stored_fact.save()
            sys_result.facts.add(stored_fact)
        sys_result.save()

    # Make this atomic for the same reason as _finalize_host.
    @transaction.atomic
    def v2_runner_on_unreachable(self, result):
        """Print a json representation of the result."""
        try:
            scan_data_log.safe_log_ansible_result(result, self.scan_task)
            result_obj = _construct_result(result)
            self.results.append(result_obj)
            logger.warning('%s', result_obj)

            # pylint: disable=protected-access
            unreachable_host = result._host.name
            result_message = result._result.get(
                'msg', 'No information given on unreachable warning.  '
                'Missing msg attribute.')
            message = 'UNREACHABLE %s. %s' % (unreachable_host,
                                              result_message)
            self.scan_task.log_message(
                message, log_level=logging.ERROR)

            self._finalize_host(
                unreachable_host, SystemInspectionResult.UNREACHABLE)
        except Exception as error:
            self.scan_task.log_message(
                'UNEXPECTED FAILURE in v2_runner_on_unreachable.'
                '  Error: %s\nAnsible result: %s' % (
                    error, result._result),
                log_level=logging.ERROR)
            traceback.print_exc()
            raise error
