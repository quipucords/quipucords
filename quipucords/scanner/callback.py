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
from ansible.plugins.callback import CallbackBase
from api.models import (ScanJob, InspectionResult,
                        SystemInspectionResult, RawFact)

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def _construct_result(result):
    """Construct result object."""
    # pylint: disable=protected-access
    host = result._host
    return {'host': host.name, 'result': result._result}


class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action.

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """

    def __init__(self, scanjob=None, inspect_results=None, display=None):
        """Create result callback."""
        super().__init__(display=display)
        self.scanjob = scanjob
        self.source = None
        if scanjob is not None:
            self.source = scanjob.source
        self.inspect_results = inspect_results
        self.results = []
        self._ansible_facts = {}

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
                    facts = self._ansible_facts[host]
                    logger.debug('host scan complete for %s with facts %s',
                                 host, facts)

                    # Update scan counts and save
                    if self.scanjob is not None:
                        self.scanjob.systems_scanned += 1
                        self.scanjob.save()

                    # Save facts for host
                    sys_result = SystemInspectionResult(
                        name=host, status=SystemInspectionResult.SUCCESS)
                    sys_result.save()
                    for result_key, result_value in facts.items():
                        stored_fact = RawFact(name=result_key,
                                              value=result_value)
                        stored_fact.save()
                        sys_result.facts.add(stored_fact)
                    sys_result.save()

                    inspect_result = self.inspect_results.results.filter(
                        source__id=self.source.id).first()
                    if inspect_result is None:
                        inspect_result = InspectionResult(source=self.source)
                        inspect_result.save()
                    inspect_result.systems.add(sys_result)
                    inspect_result.save()
                    self.inspect_results.results.add(inspect_result)
                    self.inspect_results.save()

                elif not key.startswith('internal'):
                    facts[key] = value

            if host in self._ansible_facts:
                self._ansible_facts[host].update(facts)
            else:
                self._ansible_facts[host] = facts

    def v2_runner_on_unreachable(self, result):
        """Print a json representation of the result."""
        result_obj = _construct_result(result)
        self.results.append(result_obj)
        if self.scanjob is not None:
            self._update_reachable_hosts(result_obj)
            self.scanjob.failed_scans += 1
            self.scanjob.status = ScanJob.FAILED
            self.scanjob.save()
        logger.warning('%s', result_obj)

    def _update_reachable_hosts(self, result_obj):
        if self.scanjob.scan_type != ScanJob.HOST:
            # Don't update for discovery scan.
            return

        unreachable_host = result_obj['host']
        logger.error(
            'Host %s is no longer reachable.  Moving host to failed results',
            unreachable_host)

        inspect_result = self.inspect_results.results.filter(
            source__id=self.source.id).first()
        if inspect_result is None:
            inspect_result = InspectionResult(source=self.source)
            inspect_result.save()
        sys_result = SystemInspectionResult(
            name=unreachable_host,
            status=SystemInspectionResult.UNREACHABLE)
        sys_result.save()
        inspect_result.systems.add(sys_result)
        inspect_result.save()

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Print a json representation of the result."""
        result_obj = _construct_result(result)
        self.results.append(result_obj)
        logger.error('%s', result_obj)
