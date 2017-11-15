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
from api.models import Results, ResultKeyValue

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

    def __init__(self, scanjob=None, scan_results=None, display=None):
        """Create result callback."""
        super().__init__(display=display)
        self.scanjob = scanjob
        self.scan_results = scan_results
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
                    row = Results(row=host)
                    row.save()
                    for result_key, result_value in facts.items():
                        stored_fact = ResultKeyValue(key=result_key,
                                                     value=result_value)
                        stored_fact.save()
                        row.columns.add(stored_fact)
                    row.save()
                    self.scan_results.results.add(row)
                    self.scan_results.save()

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
        logger.warning('%s', result_obj)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Print a json representation of the result."""
        result_obj = _construct_result(result)
        self.results.append(result_obj)
        logger.error('%s', result_obj)
