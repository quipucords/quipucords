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
from django.db import transaction
from ansible.plugins.callback import CallbackBase
from api.models import (ScanTask, InspectionResult,
                        SystemInspectionResult, RawFact)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def _construct_result(result):
    """Construct result object."""
    # pylint: disable=protected-access
    host = result._host
    return {'host': host.name, 'result': result._result}


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

    @transaction.atomic
    def v2_runner_on_ok(self, result):
        """Print a json representation of the result."""
        result_obj = _construct_result(result)
        self.results.append(result_obj)
        logger.debug('%s', result_obj)
        # pylint: disable=protected-access
        host = str(result._host)
        if (result._result is not None and isinstance(result._result, dict) and
                'ansible_facts' in result._result):
            host_facts = result._result['ansible_facts']
            facts = {}
            for key, value in host_facts.items():
                if key == 'host_done':
                    self.finalize_host(host)
                elif not key.startswith('internal'):
                    facts[key] = value
                # Facts starting with 'internal' are used only by the
                # Ansible playbooks to compute other
                # facts. Deliberately drop them here.

            if host in self._ansible_facts:
                self._ansible_facts[host].update(facts)
            else:
                self._ansible_facts[host] = facts

    def _result_objects(self, host, status):
        """Create and save result objects.

        Return objects will have been saved in the database. You don't
        have to save them again unless you update them.

        :returns: a pair of SystemInspectionResult, InspectionResult.
        """
        # Have to save inspect_result (if creating it) and sys_result
        # because inspect_result.systems.add wants them to have
        # primary keys first. This means that _result_objects has to
        # be part of any larger transaction that is updating the
        # database.
        inspect_result = self.inspect_results.results.filter(
            source__id=self.source.id).first()
        if inspect_result is None:
            inspect_result = InspectionResult(
                scan_task=self.scan_task, source=self.source)
            inspect_result.save()
        sys_result = SystemInspectionResult(
            name=host, status=status)
        sys_result.save()

        inspect_result.systems.add(sys_result)
        inspect_result.save()

        return sys_result, inspect_result

    # Called after all fact collection is complete for host. Writing
    # results needs to be atomic so that the host won't be marked
    # as complete unless we actually save its results.
    @transaction.atomic
    def finalize_host(self, host):
        facts = self._ansible_facts[host]
        logger.debug('host scan complete for %s with facts %s',
                     host, facts)

        # Update scan counts
        if self.scan_task is not None:
            self.scan_task.systems_scanned += 1
            self.scan_task.save()

        sys_result, inspect_result = self._result_objects(
            host, SystemInspectionResult.SUCCESS)

        # Generate facts for host
        for result_key, result_value in facts.items():
            stored_fact = RawFact(name=result_key,
                                  value=result_value)
            stored_fact.save()
            sys_result.facts.add(stored_fact)
        sys_result.save()

        self.inspect_results.results.add(inspect_result)
        self.inspect_results.save()

    # Same as above. The multiple save() statements are hidden inside
    # _update_reachable_hosts, but they do need to be in the same
    # transaction as the scan_task.save() below.
    @transaction.atomic
    def v2_runner_on_unreachable(self, result):
        """Print a json representation of the result."""
        result_obj = _construct_result(result)
        self.results.append(result_obj)
        logger.warning('%s', result_obj)

        unreachable_host = result_obj['host']
        logger.error(
            'Host %s is no longer reachable.  Moving host to failed results',
            unreachable_host)

        sys_result, inspect_result = self._result_objects(
            unreachable_host, SystemInspectionResult.UNREACHABLE)

        self.scan_task.systems_failed += 1
        self.scan_task.status = ScanTask.FAILED
        self.scan_task.save()

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Print a json representation of the result."""
        result_obj = _construct_result(result)
        self.results.append(result_obj)
        logger.error('%s', result_obj)
