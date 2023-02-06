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

import log_messages
from api.connresult.model import SystemConnectionResult
from scanner.network.utils import STOP_STATES

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ConnectResultCallback:
    """Record connection results.

    SystemConnectionResult objects are created for every machine we
    scan, as we scan it.
    """

    # pylint: disable=protected-access,too-many-arguments
    def __init__(self, result_store, credential, source, manager_interrupt):
        """Create result callback."""
        self.result_store = result_store
        self.credential = credential
        self.source = source
        self.interrupt = manager_interrupt
        self.stopped = False

    def task_on_ok(self, event_data, host, task_result):
        """Print a json representation of the event_data on ok."""
        try:
            if "rc" in task_result and task_result["rc"] == 0:
                self.result_store.record_result(
                    host, self.source, self.credential, SystemConnectionResult.SUCCESS
                )
            logger.debug("%s", {"host": host, "result": task_result})
        except Exception as error:
            self.result_store.scan_task.log_message(
                log_messages.TASK_UNEXPECTED_FAILURE
                % ("task_on_ok", error, event_data),
                log_level=logging.ERROR,
            )
            traceback.print_exc()
            raise error

    def task_on_unreachable(self, event_data, host, task_result):
        """Print a json representation of the event_data on unreachable."""
        try:
            result_message = task_result.get(
                "msg", "No information given on unreachable warning."
            )
            ssl_ansible_auth_error = (
                result_message is not None
                and "permission denied" in result_message.lower()
            )
            if not ssl_ansible_auth_error:
                # host is unreachable
                self.result_store.record_result(
                    host,
                    self.source,
                    self.credential,
                    SystemConnectionResult.UNREACHABLE,
                )
            else:
                # invalid creds
                self.result_store.scan_task.log_message(
                    log_messages.TASK_PERMISSION_DENIED % (host, self.credential.name)
                )
            logger.debug("%s", {"host": host, "result": task_result})
        except Exception as error:
            self.result_store.scan_task.log_message(
                log_messages.TASK_UNEXPECTED_FAILURE
                % ("task_on_unreachable", error, event_data),
                log_level=logging.ERROR,
            )
            traceback.print_exc()
            raise error

    def task_on_failed(self, event_data, host, task_result):
        """Print a json representation of the event_data on failed."""
        # pylint: disable=protected-access
        try:
            result_message = task_result.get(
                "stderr", "No information given on failure."
            )
            authentication_error = (
                result_message is not None
                and "permission denied" in result_message.lower()
            )
            if not authentication_error:
                # failure is not authentication
                message = f"FAILED {host}. {result_message}"
                self.result_store.scan_task.log_message(
                    message, log_level=logging.ERROR
                )
            else:
                # invalid creds
                self.result_store.scan_task.log_message(
                    log_messages.TASK_PERMISSION_DENIED % (host, self.credential.name)
                )
            logger.debug("%s", {"host": host, "result": task_result})
        except Exception as error:
            self.result_store.scan_task.log_message(
                log_messages.TASK_UNEXPECTED_FAILURE
                % ("task_on_failed", error, event_data),
                log_level=logging.ERROR,
            )
            traceback.print_exc()
            raise error

    def event_callback(self, event_dict=None):
        """Control the event callback for runner."""
        if event_dict:
            event = event_dict.get("event")
            event_data = event_dict.get("event_data")
            unexpected_error = False
            ignore_states = ["runner_on_start"]
            if event in ignore_states:
                return
            if "runner" in event:
                host = event_data.get("host")
                task_result = event_data.get("res")
                if None not in (host, task_result):
                    if event == "runner_on_ok":
                        self.task_on_ok(event_data, host, task_result)
                    elif event == "runner_on_unreachable":
                        self.task_on_unreachable(event_data, host, task_result)
                    elif event == "runner_on_failed":
                        self.task_on_failed(event_data, host, task_result)
                    else:
                        unexpected_error = True
                else:
                    unexpected_error = True
                if unexpected_error:
                    self.result_store.scan_task.log_message(
                        log_messages.TASK_UNEXPECTED_FAILURE
                        % ("runner_event", f"Unknown State ({event})", event_dict),
                        log_level=logging.ERROR,
                    )

    def cancel_callback(self):
        """Control the cancel callback for runner."""
        if self.stopped:
            return True
        for stop_type, stop_value in STOP_STATES.items():
            if self.interrupt.value == stop_value:
                self.result_store.scan_task.log_message(
                    log_messages.NETWORK_CALLBACK_ACK_STOP % ("CONNECT", stop_type),
                    log_level=logging.INFO,
                )
                self.stopped = True
                return True
        return False
