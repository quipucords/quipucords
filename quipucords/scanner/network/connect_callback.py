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

import logging
import traceback

from api.connresult.model import SystemConnectionResult

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ConnectResultCallback():
    """Record connection results.

    SystemConnectionResult objects are created for every machine we
    scan, as we scan it.
    """

    # pylint: disable=protected-access
    def __init__(self, result_store, credential, source):
        """Create result callback."""
        self.result_store = result_store
        self.credential = credential
        self.source = source

    def task_on_ok(self, event_data):
        """Print a json representation of the event_data on ok."""
        try:
            host = event_data.get('host')
            task_result = event_data.get('res')
            if 'rc' in task_result and task_result['rc'] == 0:
                self.result_store.record_result(host,
                                                self.source,
                                                self.credential,
                                                SystemConnectionResult.SUCCESS)
            else:
                self.result_store.record_result(host,
                                                self.source,
                                                self.credential,
                                                SystemConnectionResult.FAILED)
            logger.debug('%s', {'host': host, 'result': task_result})
        except Exception as error:
            self.result_store.scan_task.log_message(
                'UNEXPECTED FAILURE in v2_runner_on_ok.'
                '  Error: %s\nAnsible result: %s' % (
                    error, event_data),
                log_level=logging.ERROR)
            traceback.print_exc()
            raise error

    def task_on_unreachable(self, event_data):
        """Print a json representation of the event_data on unreachable."""
        try:
            host = event_data['host']
            task_result = event_data['res']
            result_message = task_result.get(
                'msg',
                'No information given on unreachable warning.')
            ssl_ansible_auth_error = result_message is not None and \
                'permission denied' in result_message.lower()
            if not ssl_ansible_auth_error:
                # host is unreachable
                self.result_store.record_result(
                    host,
                    self.source,
                    self.credential,
                    SystemConnectionResult.UNREACHABLE)
            else:
                # invalid creds
                message = 'PERMISSION DENIED %s could not connect'\
                    ' with cred %s.' % (host, self.credential.name)
                self.result_store.scan_task.log_message(message)
                self.result_store.record_result(host,
                                                self.source,
                                                self.credential,
                                                SystemConnectionResult.FAILED)
            logger.debug('%s', {'host': host, 'result': task_result})
        except Exception as error:
            self.result_store.scan_task.log_message(
                'UNEXPECTED FAILURE in v2_runner_on_unreachable.'
                '  Error: %s\nAnsible result: %s' % (
                    error, event_data),
                log_level=logging.ERROR)
            traceback.print_exc()
            raise error

    def task_on_failed(self, event_data):
        """Print a json representation of the event_data on failed."""
        # pylint: disable=protected-access
        try:
            host = event_data['host']
            task_result = event_data['res']
            result_message = task_result.get(
                'stderr',
                'No information given on failure.')
            authentication_error = result_message is not None and \
                'permission denied' in result_message.lower()
            if not authentication_error:
                # failure is not authentication
                message = 'FAILED %s. %s' % (host, result_message)
                self.result_store.scan_task.log_message(
                    message, log_level=logging.ERROR)
            else:
                # invalid creds
                message = 'PERMISSION DENIED %s could not connect'\
                    ' with cred %s.' % (host, self.credential.name)
                self.result_store.scan_task.log_message(message)
            logger.debug('%s', {'host': host, 'result': task_result})
            self.result_store.record_result(host,
                                            self.source,
                                            self.credential,
                                            SystemConnectionResult.FAILED)
        except Exception as error:
            self.result_store.scan_task.log_message(
                'UNEXPECTED FAILURE in v2_runner_on_failed.'
                '  Error: %s\nAnsible result: %s' % (
                    error, event_data),
                log_level=logging.ERROR)
            traceback.print_exc()
            raise error

    def runner_event(self, event_dict=None):
        """Control the event callback for runner."""
        if event_dict:
            event = event_dict.get('event')
            event_data = event_dict.get('event_data')
            if 'runner' in event_dict['event']:
                if event == 'runner_on_ok':
                    self.task_on_ok(event_data)
                elif event == 'runner_on_unreachable':
                    self.task_on_unreachable(event_data)
                elif event == 'runner_on_failed':
                    self.task_on_failed(event_data)
                else:
                    self.result_store.scan_task.log_message(
                        'UNEXPECTED FAILURE in runner_event.'
                        '   Error Unknown State: %s\nAnsible result: %s' % (
                            event_dict['event'],
                            event_dict), log_level=logging.ERROR)
