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
"""Callback object for capturing ansible task execution."""

import logging
import json
from django.db import transaction
from ansible.plugins.callback import CallbackBase
from api.models import (InspectionResult,
                        SystemInspectionResult,
                        RawFact)
from scanner.network.processing import process

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

ANSIBLE_FACTS = 'ansible_facts'
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
    key = result._task.register or NO_KEY
    return {HOST: host.name, RESULT: result._result, KEY: key}


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
        if ANSIBLE_FACTS in result._result:
            return [(key, value)
                    for key, value in result._result[ANSIBLE_FACTS].items()
                    if not key.startswith(INTERNAL_)]
            # return list(result._result[ANSIBLE_FACTS].items())
        elif (isinstance(result._task.register, str) and
              not result._task.register.startswith(INTERNAL_)):
            return [(result._task.register, result._result)]

    return []


class InspectResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action.

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """

    def __init__(self, scan_task, inspect_results, display=None):
        """Create result callback."""
        super().__init__(display=display)
        self.scan_task = scan_task
        self.source = scan_task.source
        self.inspect_results = inspect_results
        self.results = []
        self._ansible_facts = {}

    # Ansible considers tasks failed when their return code is
    # nonzero, even if we set ignore_errors=True. We want to be able
    # to process those task results, so we need to handle failed
    # results the same way we treat ok ones.
    def v2_runner_on_ok(self, result):
        """Print a json representation of the result."""
        self.handle_result(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Print a json representation of the result."""
        self.handle_result(result)

    def handle_result(self, result):
        """Handle an incoming result object."""
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
        for key, value in results_to_store:
            if key == HOST_DONE:
                self._finalize_host(host)
            else:
                host_facts[key] = value

        if host in self._ansible_facts:
            self._ansible_facts[host].update(host_facts)
        else:
            self._ansible_facts[host] = host_facts

    def _get_inspect_result(self):
        # Have to save inspect_result (if creating it) because
        # inspect_result.systems.add wants it to have a primary key
        # first. This means that _inspect_result has to be part of any
        # larger transaction that is updating the database.
        inspect_result = self.inspect_results.results.filter(
            source__id=self.source.id).first()
        if inspect_result is None:
            inspect_result = InspectionResult(
                scan_task=self.scan_task, source=self.source)
            inspect_result.save()

        return inspect_result

    # Called after all fact collection is complete for host. Writing
    # results needs to be atomic so that the host won't be marked
    # as complete unless we actually save its results.
    @transaction.atomic
    def _finalize_host(self, host):
        facts = self._ansible_facts.get(host, {})
        results = process.process(facts, host)

        logger.debug('host scan complete for %s with facts %s',
                     host, results)

        # Update scan counts
        if self.scan_task is not None:
            self.scan_task.systems_scanned += 1
            self.scan_task.save()

        inspect_result = self._get_inspect_result()
        sys_result = SystemInspectionResult(
            name=host, status=SystemInspectionResult.SUCCESS)
        sys_result.save()

        inspect_result.systems.add(sys_result)
        inspect_result.save()

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

        self.inspect_results.results.add(inspect_result)
        self.inspect_results.save()

    # Make this atomic for the same reason as _finalize_host.
    @transaction.atomic
    def v2_runner_on_unreachable(self, result):
        """Print a json representation of the result."""
        result_obj = _construct_result(result)
        self.results.append(result_obj)
        logger.warning('%s', result_obj)

        unreachable_host = result_obj[HOST]
        logger.error(
            'Host %s is no longer reachable.  Moving host to failed results',
            unreachable_host)

        self._get_inspect_result()
        sys_result = SystemInspectionResult(
            name=unreachable_host,
            status=SystemInspectionResult.UNREACHABLE)
        sys_result.save()

        self.scan_task.systems_failed += 1
