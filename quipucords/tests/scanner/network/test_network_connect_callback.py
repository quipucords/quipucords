"""Test the connect callback capabilities."""

# pylint: disable=ungrouped-imports
from unittest.mock import Mock

from django.test import TestCase

from api.models import Credential, ScanJob, ScanTask, Source
from scanner.network.connect import ConnectResultStore
from scanner.network.connect_callback import ConnectResultCallback
from scanner.network.utils import STOP_STATES
from tests.scanner.test_util import create_scan_job


def build_event(host, return_code=0, stderr=False, msg=False, event=False):
    """Build event dictionary matching ansible runner response."""
    res_dict = {"rc": return_code}
    if stderr:
        res_dict["stderr"] = stderr
    if msg:
        res_dict["msg"] = msg
    event_data = {"host": host, "res": res_dict}
    event_dict = {"event": event, "event_data": event_data}
    return event_dict


# pylint: disable=too-many-instance-attributes
class TestConnectResultCallback(TestCase):
    """Test ConnectResultCallback."""

    def setUp(self):
        """Set up required for tests."""
        self.cred = Credential(
            name="cred1",
            username="username",
            password="password",
            ssh_keyfile="keyfile",
            become_method="sudo",
            become_user="root",
            become_password="become",
        )
        self.cred.save()

        self.source = Source(
            name="source1",
            hosts=["1.2.3.4", "1.2.3.5", "1.2.3.6"],
            source_type="network",
            port=22,
        )
        self.source.save()
        self.source.credentials.add(self.cred)
        self.source.save()

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT
        )
        self.interrupt = Mock(value=ScanJob.JOB_RUN)

    def test_task_on_ok(self):
        """Test the callback on ok."""
        results_store = ConnectResultStore(self.scan_task)
        self.interrupt.return_value.value = ScanJob.JOB_RUN
        callback = ConnectResultCallback(
            results_store, self.cred, self.source, self.interrupt
        )
        events = []
        events.append(build_event(host="1.2.3.4", event="runner_on_ok"))
        events.append(build_event(host="1.2.3.5", return_code=1, event="runner_on_ok"))
        events.append(
            build_event(host="1.2.3.6", return_code=None, event="runner_on_ok")
        )
        for event in events:
            callback.event_callback(event)
        self.assertEqual(callback.result_store.scan_task.systems_count, 3)
        self.assertEqual(callback.result_store.scan_task.systems_scanned, 1)
        self.assertEqual(callback.result_store.scan_task.systems_failed, 0)

    def test_task_on_failed(self):
        """Test the callback on failed."""
        results_store = ConnectResultStore(self.scan_task)
        callback = ConnectResultCallback(
            results_store, self.cred, self.source, self.interrupt
        )
        events = []
        events.append(build_event(host="1.2.3.4", event="runner_on_failed"))
        events.append(
            build_event(
                host="1.2.3.5", event="runner_on_failed", stderr="permission denied"
            )
        )
        for event in events:
            callback.event_callback(event)
        self.assertEqual(callback.result_store.scan_task.systems_failed, 0)
        self.assertEqual(callback.result_store.scan_task.systems_count, 3)

    def test_task_on_unreachable(self):
        """Test the callback on unreachable."""
        results_store = ConnectResultStore(self.scan_task)
        callback = ConnectResultCallback(
            results_store, self.cred, self.source, self.interrupt
        )
        events = []
        events.append(build_event(host="1.2.3.4", event="runner_on_unreachable"))
        events.append(
            build_event(
                host="1.2.3.5", event="runner_on_unreachable", msg="permission denied"
            )
        )
        for event in events:
            callback.event_callback(event)
        self.assertEqual(callback.result_store.scan_task.systems_failed, 0)
        self.assertEqual(callback.result_store.scan_task.systems_unreachable, 1)
        self.assertEqual(callback.result_store.scan_task.systems_count, 3)

    def test_exceptions_for_tasks(self):
        """Test exception for each task."""
        results_store = None
        callback = ConnectResultCallback(
            results_store, self.cred, self.source, self.interrupt
        )
        events = []
        events.append(build_event(host="1.2.3.4", event="runner_on_ok"))
        events.append(build_event(host="1.2.3.4", event="runner_on_failed"))
        events.append(build_event(host="1.2.3.4", event="runner_on_unreachable"))
        for event in events:
            with self.assertRaises(Exception):
                callback.event_callback(event)

    def test_unknown_event_response(self):
        """Test unknown event response."""
        results_store = ConnectResultStore(self.scan_task)
        callback = ConnectResultCallback(
            results_store, self.cred, self.source, self.interrupt
        )
        event = build_event(host="1.2.3.4", event="runner_on_unknown_event")
        callback.event_callback(event)

    def test_empty_host(self):
        """Test unknown event response."""
        results_store = ConnectResultStore(self.scan_task)
        callback = ConnectResultCallback(
            results_store, self.cred, self.source, self.interrupt
        )
        event = build_event(host=None, event="runner_on_ok")
        callback.event_callback(event)

    def test_cancel_event(self):
        """Test cancel event response."""
        # Test continue state
        results_store = ConnectResultStore(self.scan_task)
        callback = ConnectResultCallback(
            results_store, self.cred, self.source, self.interrupt
        )
        result = callback.cancel_callback()
        self.assertEqual(result, False)
        # Test cancel state
        for stop_value in STOP_STATES.values():
            self.interrupt = Mock(value=stop_value)
            callback = ConnectResultCallback(
                results_store, self.cred, self.source, self.interrupt
            )
            self.assertEqual(callback.interrupt.value, stop_value)
            result = callback.cancel_callback()
            self.assertEqual(result, True)
