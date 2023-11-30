"""Test the connect callback capabilities."""

from unittest.mock import Mock

import pytest

from api.models import Source
from constants import DataSources
from scanner.network.connect import ConnectResultStore
from scanner.network.connect_callback import ConnectResultCallback
from scanner.network.utils import STOP_STATES
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
        results_store = ConnectResultStore(ScanTaskFactory(source=source))
        callback = ConnectResultCallback(
            results_store, source.single_credential, source, Mock()
        )
        events = []
        events.append(build_event(host="1.2.3.4", event="runner_on_ok"))
        events.append(build_event(host="1.2.3.5", return_code=1, event="runner_on_ok"))
        events.append(
            build_event(host="1.2.3.6", return_code=None, event="runner_on_ok")
        )
        for event in events:
            callback.event_callback(event)
        callback.result_store.scan_task.systems_count == 3
        callback.result_store.scan_task.systems_scanned == 1
        callback.result_store.scan_task.systems_failed == 0

    def test_task_on_failed(self, source: Source):
        """Test the callback on failed."""
        results_store = ConnectResultStore(ScanTaskFactory(source=source))
        callback = ConnectResultCallback(
            results_store, source.single_credential, source, Mock()
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
        results_store = ConnectResultStore(ScanTaskFactory(source=source))
        callback = ConnectResultCallback(
            results_store, source.single_credential, source, Mock()
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
        callback.result_store.scan_task.systems_failed == 0
        callback.result_store.scan_task.systems_unreachable == 1
        callback.result_store.scan_task.systems_count == 3

    def test_exceptions_for_tasks(self, source: Source):
        """Test exception for each task."""
        results_store = None
        callback = ConnectResultCallback(
            results_store, source.single_credential, source, Mock()
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
            results_store, source.single_credential, source, Mock()
        )
        event = build_event(host="1.2.3.4", event="runner_on_unknown_event")
        callback.event_callback(event)

    def test_empty_host(self, source: Source):
        """Test unknown event response."""
        results_store = ConnectResultStore(ScanTaskFactory())
        callback = ConnectResultCallback(
            results_store, source.single_credential, source, Mock()
        )
        event = build_event(host=None, event="runner_on_ok")
        callback.event_callback(event)

    def test_cancel_event(self, source: Source):
        """Test cancel event response."""
        # Test continue state
        results_store = ConnectResultStore(ScanTaskFactory(source=source))
        callback = ConnectResultCallback(
            results_store, source.single_credential, source, Mock()
        )
        result = callback.cancel_callback()
        assert not result
        # Test cancel state
        for stop_value in STOP_STATES.values():
            interrupt = Mock(value=stop_value)
            callback = ConnectResultCallback(
                results_store, source.single_credential, source, interrupt
            )
            assert callback.interrupt.value == stop_value
            result = callback.cancel_callback()
            assert result is True
