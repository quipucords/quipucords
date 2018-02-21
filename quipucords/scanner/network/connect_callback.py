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
from api.connresults.model import SystemConnectionResult
from scanner import input_log

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def _construct_result(result):
    """Construct result object."""
    # pylint: disable=protected-access
    host = result._host
    return {'host': host.name, 'result': result._result}


class ConnectResultCallback(CallbackBase):
    """Record connection results.

    SystemConnectionResult objects are created for every machine we
    scan, as we scan it.
    """

    def __init__(self, result_store, credential, scan_task, display=None):
        """Create result callback."""
        super().__init__(display=display)
        self.result_store = result_store
        self.credential = credential
        self.scan_task = scan_task

    def v2_runner_on_ok(self, result):
        """Print a json representation of the result."""
        input_log.log_ansible_result(result, self.scan_task)
        host = result._host.name      # pylint: disable=protected-access
        task_result = result._result  # pylint: disable=protected-access
        if 'rc' in task_result and task_result['rc'] == 0:
            self.result_store.record_result(host,
                                            self.credential,
                                            SystemConnectionResult.SUCCESS)

        result_obj = _construct_result(result)
        logger.debug('%s', result_obj)

    def v2_runner_on_unreachable(self, result):
        """Print a json representation of the result."""
        input_log.log_ansible_result(result, self.scan_task)
        # pylint: disable=protected-access
        host = result._host.name
        result_message = result._result.get(
            'msg', 'No information given on unreachable warning.  '
            'Missing msg attribute.')
        message = 'UNREACHABLE %s. %s' % (host, result_message)
        self.result_store.scan_task.log_message(
            message, log_level=logging.WARN)
        result_obj = _construct_result(result)
        logger.debug('%s', result_obj)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Print a json representation of the result."""
        input_log.log_ansible_result(result, self.scan_task)
        # pylint: disable=protected-access
        host = result._host.name
        result_message = result._result.get(
            'stderr', 'No information given on failure.  '
            'Missing stderr attribute.')
        message = 'FAILED %s. %s' % (host, result_message)
        self.result_store.scan_task.log_message(
            message, log_level=logging.ERROR)
        result_obj = _construct_result(result)
        logger.debug('%s', result_obj)
