"""Test the connect callback capabilities."""

import logging
from unittest.mock import Mock

import pytest

from api.models import Source
from api.scantask.model import ScanTask
from constants import DataSources
from scanner.network.connect_callback import ConnectResultCallback
from scanner.network.inspect import ConnectResultStore
from tests.factories import ScanTaskFactory, SourceFactory


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


@pytest.fixture
def source():
    """Return a source instance for testing."""
    return SourceFactory(
        source_type=DataSources.NETWORK,
        hosts=["1.2.3.4", "1.2.3.5", "1.2.3.6"],
    )


@pytest.mark.django_db
class TestConnectResultCallback:
    """Test ConnectResultCallback."""

    def test_task_on_ok(self, source: Source):
        """Test the callback on ok."""
        results_store = ConnectResultStore(
            ScanTaskFactory(source=source, scan_type=ScanTask.SCAN_TYPE_INSPECT)
        )
        callback = ConnectResultCallback(
            results_store, source.single_credential, source
        )
        events = []
        events.append(build_event(host="1.2.3.4", event="runner_on_ok"))
        events.append(build_event(host="1.2.3.5", return_code=1, event="runner_on_ok"))
        events.append(
            build_event(host="1.2.3.6", return_code=None, event="runner_on_ok")
        )
        for event in events:
            callback.event_callback(event)
        assert callback.result_store.scan_task.systems_count == 3
        assert callback.result_store.scan_task.systems_scanned == 1
        assert callback.result_store.scan_task.systems_failed == 0

    def test_task_on_failed(self, source: Source):
        """Test the callback on failed."""
        results_store = ConnectResultStore(ScanTaskFactory(source=source))
        callback = ConnectResultCallback(
            results_store, source.single_credential, source
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
        assert callback.result_store.scan_task.systems_failed == 0
        assert callback.result_store.scan_task.systems_count == 3

    def test_task_on_unreachable(self, source: Source):
        """Test the callback on unreachable."""
        results_store = ConnectResultStore(
            ScanTaskFactory(source=source, scan_type=ScanTask.SCAN_TYPE_INSPECT)
        )
        callback = ConnectResultCallback(
            results_store, source.single_credential, source
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
        assert callback.result_store.scan_task.systems_failed == 0
        assert callback.result_store.scan_task.systems_unreachable == 1
        assert callback.result_store.scan_task.systems_count == 3

    def test_exceptions_for_tasks(self, source: Source):
        """Test exception for each task."""
        results_store = None
        callback = ConnectResultCallback(
            results_store, source.single_credential, source
        )
        events = []
        events.append(build_event(host="1.2.3.4", event="runner_on_ok"))
        events.append(build_event(host="1.2.3.4", event="runner_on_failed"))
        events.append(build_event(host="1.2.3.4", event="runner_on_unreachable"))
        for event in events:
            # TODO: rewrite this test to something more meaningful. results_store set
            # as None will cause attribute error in many places and don't really reflect
            # a expected error.
            with pytest.raises(AttributeError):
                callback.event_callback(event)

    def test_unknown_event_response(self, source: Source):
        """Test unknown event response."""
        results_store = ConnectResultStore(ScanTaskFactory(source=source))
        callback = ConnectResultCallback(
            results_store, source.single_credential, source
        )
        event = build_event(host="1.2.3.4", event="runner_on_unknown_event")
        callback.event_callback(event)

    def test_empty_host(self, source: Source):
        """Test unknown event response."""
        results_store = ConnectResultStore(ScanTaskFactory())
        callback = ConnectResultCallback(
            results_store, source.single_credential, source
        )
        event = build_event(host=None, event="runner_on_ok")
        callback.event_callback(event)

    def test_unexpected_event(self):
        """Test how event_callback handles an unexpected event."""
        results_store = Mock()
        callback = ConnectResultCallback(results_store, Mock(), Mock())
        event_data = {"some_data": "some_value"}
        assert callback.event_callback(event_data) is None
        expected_error = (
            "UNEXPECTED FAILURE in runner_event. Error: None\n"
            "Ansible result: {'some_data': 'some_value'}"
        )
        callback.result_store.scan_task.log_message.assert_called_with(
            expected_error, log_level=logging.ERROR
        )
