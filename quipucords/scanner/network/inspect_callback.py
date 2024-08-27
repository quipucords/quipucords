"""Callback object for capturing ansible task execution."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Generator

from django.conf import settings

import log_messages
from api.inspectresult.model import InspectResult
from utils.misc import sanitize_for_utf8_compatibility

logger = logging.getLogger(__name__)

HOST_DONE = "host_done"
TIMEOUT_RC = 124  # 'timeout's return code when it times out.
UNKNOWN_HOST = "unknown_host"
UNKNOWN_TASK_PATH = "unknown_task_path"


@dataclass
class AnsibleResults:
    """Host state and facts collected from ansible events."""

    host: str
    status: str
    facts: dict


class InspectCallback:
    """Callback helper to plug ansible callbacks for network scan inspection phase."""

    def __init__(self):
        self._ansible_facts = defaultdict(dict)
        self._unreachable_hosts = set()
        self._collect_skipped_tasks_enabled = (
            settings.QUIPUCORDS_FEATURE_FLAGS.is_feature_active("REPORT_SKIPPED_TASKS")
        )
        self._skipped_facts = defaultdict(set)
        self.stopped = False

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
        logger.debug("[host=%s] processing role='%s' task='%s'", host, role, task)
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
            logger.error("[host=%s role='%s' task='%s'] timed out", host, role, task)

        # Only log an error when ignore errors is false
        if event_data.get("ignore_errors", False):
            err_reason = result.get("msg", event_data)
            logger.warning(
                "[host=%s role='%s' task='%s'] failed - reason: %s",
                host,
                role,
                task,
                err_reason,
            )

        task_facts = result.get("ansible_facts")
        if task_facts:
            # only keeping process task facts here because legacy callback had it
            # but do we really want to collect facts for a failed event?
            # TODO: keep an eye on logs from test lab and field for the following
            logger.warning(
                "[host=%s role='%s' task='%s'] FAILED and contains ansible_facts",
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

    def task_on_skipped(self, event_dict):
        """Handle skipped events.

        This is only run when REPORT_SKIPPED_TASKS feature flag is active.
        event_callback checks for the flag, so we don't need to do it here.
        """
        event_data = event_dict.get("event_data", {})
        host = event_data.get("host", UNKNOWN_HOST)
        task_path = event_data.get("task_path", UNKNOWN_TASK_PATH)
        result = event_data.get("res", {})
        loop_var_name = result.get("ansible_loop_var", "")
        item_id = result.get(loop_var_name, "")
        task_id = task_path
        if item_id:
            task_id = f"{task_path}[{item_id}]"

        logger.debug("[host=%s] skipped task %s, item='%s'", host, task_path, item_id)
        self._skipped_facts[host].add(task_id)

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
        skipped = ["runner_on_skipped", "runner_item_on_skipped"]
        runner_ignore = ["runner_on_start"]
        if not self._collect_skipped_tasks_enabled:
            runner_ignore.extend(skipped)
            skipped = []

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
        elif event in skipped:
            self.task_on_skipped(event_dict)

    def cancel_callback(self):
        """Control the cancel callback for ansible runner."""
        if self.stopped:
            return True
        return False
