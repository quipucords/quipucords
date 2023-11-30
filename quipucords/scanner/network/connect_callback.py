"""Callback object for capturing ansible task execution."""

import logging
import traceback

import log_messages
from api.connresult.model import SystemConnectionResult
from scanner.network.utils import STOP_STATES

logger = logging.getLogger(__name__)


class UnexpectedError(Exception):
    """Unexpected error when parsing event data from Ansible Runner."""


class ConnectResultCallback:
    """Record connection results.

    SystemConnectionResult objects are created for every machine we
    scan, as we scan it.
    """

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
            logger.exception("Uncaught exception during Ansible Runner event parsing")
            self.result_store.scan_task.log_message(
                log_messages.TASK_UNEXPECTED_FAILURE
                % ("task_on_ok", error, event_data),
                log_level=logging.ERROR,
            )
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
        try:
            self._event_callback(event_dict)
        except UnexpectedError as err:
            logger.error(str(err))
            event = event_dict.get("event")
            self.result_store.scan_task.log_message(
                log_messages.TASK_UNEXPECTED_FAILURE
                % ("runner_event", event, event_dict),
                log_level=logging.ERROR,
            )

    def _event_callback(self, event_dict=None):
        """Control the event callback for runner."""
        if event_dict:
            logger.debug("processing event callback")
            logger.debug("event_dict=%s", event_dict)
            event = event_dict.get("event")
            event_data = event_dict.get("event_data")
            ignore_states = ["runner_on_start"]
            if event is None:
                raise UnexpectedError("event is None")
            if event in ignore_states:
                return
            if event.startswith("runner"):
                host = event_data.get("host")
                task_result = event_data.get("res")
                if host is None or task_result is None:
                    raise UnexpectedError("Host or task_result is None")
                if event == "runner_on_ok":
                    self.task_on_ok(event_data, host, task_result)
                elif event == "runner_on_unreachable":
                    self.task_on_unreachable(event_data, host, task_result)
                elif event == "runner_on_failed":
                    self.task_on_failed(event_data, host, task_result)
                else:
                    raise UnexpectedError(f"Unexpected event={event}")

    def cancel_callback(self):
        """Control the cancel callback for runner."""
        if self.stopped:
            return True
        if not self.interrupt:
            return False
        for stop_type, stop_value in STOP_STATES.items():
            if self.interrupt.value == stop_value:
                self.result_store.scan_task.log_message(
                    log_messages.NETWORK_CALLBACK_ACK_STOP % ("CONNECT", stop_type),
                    log_level=logging.INFO,
                )
                self.stopped = True
                return True
        return False
