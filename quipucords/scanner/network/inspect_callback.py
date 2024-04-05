"""Callback object for capturing ansible task execution."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Generator

import log_messages
from api.inspectresult.model import InspectResult
from scanner.network.utils import STOP_STATES
from utils.misc import sanitize_for_utf8_compatibility

logger = logging.getLogger(__name__)

HOST_DONE = "host_done"
TIMEOUT_RC = 124  # 'timeout's return code when it times out.
UNKNOWN_HOST = "unknown_host"


@dataclass
class AnsibleResults:
    """Host state and facts collected from ansible events."""

    host: str
    status: str
    facts: dict


class InspectCallback:
    """Callback helper to plug ansible callbacks for network scan inspection phase."""

    def __init__(self, manager_interrupt):
        self._ansible_facts = defaultdict(dict)
        self._unreachable_hosts = set()
        self.stopped = False
        self.interrupt = manager_interrupt

    def iter_results(self) -> Generator[AnsibleResults]:
        """Yield host completion state and ansible facts."""
        for host, facts in self._ansible_facts.items():
            if host in self._unreachable_hosts:
                host_status = InspectResult.UNREACHABLE
            elif facts.get(HOST_DONE, False) is True:
                # host_done is the last fact - we assume a host is successfully scanned
                # if this fact is set to true
                host_status = InspectResult.SUCCESS
            else:
                host_status = InspectResult.FAILED
            yield AnsibleResults(host=host, status=host_status, facts=facts)

    def task_on_ok(self, event_dict: dict):
        """Handle successful ansible events."""
        event_data = event_dict.get("event_data", {})
        ansible_facts = event_data.get("res", {}).get("ansible_facts", {})
        if not ansible_facts:
            return
        host = event_data.get("host", UNKNOWN_HOST)
        task = event_data.get("task")
        role = event_data.get("role")
        logger.info("[host=%s] processing role='%s' task='%s'", host, role, task)
        self._process_task_facts(ansible_facts, host)

    def _process_task_facts(self, ansible_facts, host):
        for fact_name, _fact_value in ansible_facts.items():
            fact_value = sanitize_for_utf8_compatibility(_fact_value)
            if _fact_value != fact_value:
                logger.warning(
                    (
                        "[host=%s] Sanitized value for '%s' changed from its "
                        "original value."
                    ),
                    host,
                    fact_name,
                )
            if fact_name in self._ansible_facts[host]:
                logger.warning("[host=%s] Overwriting fact %s", host, fact_name)
            logger.debug("[host=%s] Storing fact %s", host, fact_name)
            self._ansible_facts[host][fact_name] = fact_value

    def task_on_failed(self, event_dict):
        """Handle failure events."""
        event_data = event_dict.get("event_data", {})
        host = event_data.get("host", UNKNOWN_HOST)
        result = event_data.get("res")
        task = event_data.get("task")
        role = event_data.get("role")
        if result.get("rc") == TIMEOUT_RC:
            logger.error("[host=%s] Task '%s' timed out", host, task)

        # Only log an error when ignore errors is false
        if event_data.get("ignore_errors", False):
            err_reason = result.get("msg", event_data)
            logger.warning("[host=%s] failed - reason: %s", host, err_reason)

        task_facts = result.get("ansible_facts")
        if task_facts:
            # only keeping process task facts here because legacy callback had it
            # but do we really want to collect facts for a failed event?
            # TODO: keep an eye on logs from test lab and field for the following
            logger.warning(
                "[host=%s] role='%s' task='%s' FAILED and contains ansible_facts",
                host,
                role,
                task,
            )
            self._process_task_facts(task_facts, host)

    def task_on_unreachable(self, event_dict):
        """Handle unreachable events."""
        event_data = event_dict.get("event_data", {})
        host = event_data.get("host", UNKNOWN_HOST)
        result = event_data.get("res", {})
        error_msg = result.get("msg", "No information given on unreachable error.")
        logger.error("[host=%s] UNREACHABLE - %s", host, error_msg)
        self._unreachable_hosts.add(host)

    def event_callback(self, event_dict=None):
        """
        Handle ansible events.

        Meant to be "plugged" to ansible-runner on "event_handler".

        https://ansible.readthedocs.io/projects/runner/en/stable/python_interface/?highlight=callback#runner-event-handler
        TODO: find documentation for these events.
        """
        logger.debug("processing event")
        logger.debug("event_dict=%s", event_dict)
        okay = ["runner_on_ok", "runner_item_on_ok"]
        failed = ["runner_on_failed", "runner_item_on_failed"]
        unreachable = ["runner_on_unreachable"]
        runner_ignore = [
            "runner_on_skipped",
            "runner_item_on_skipped",
            "runner_on_start",
        ]
        try:
            event = event_dict["event"]
        except KeyError:
            # since the upgrade to ansible-core 8, weird events without "event" pop up
            # given how frequent and innocuous they are, log them only at debug level
            logger.debug(
                log_messages.TASK_UNEXPECTED_FAILURE,
                "event_callback",
                "'unknown event'",
                event_dict,
            )
            return
        if event in runner_ignore:
            return
        elif event in okay:
            self.task_on_ok(event_dict)
        elif event in failed:
            self.task_on_failed(event_dict)
        elif event in unreachable:
            self.task_on_unreachable(event_dict)

    def cancel_callback(self):
        """Control the cancel callback for ansible runner."""
        if self.stopped:
            return True
        if not self.interrupt:
            return False
        for stop_type, stop_value in STOP_STATES.items():
            if self.interrupt.value == stop_value:
                logger.info(
                    log_messages.NETWORK_CALLBACK_ACK_STOP, "INSPECT", stop_type
                ),
                self.stopped = True
                return True
        return False
