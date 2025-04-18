"""Test the scanner.tasks.get_task_runner_class function."""

import logging

import pytest

from api.scantask.model import ScanTask
from scanner import tasks
from scanner.network import InspectTaskRunner as NetworkInspectTaskRunner


@pytest.mark.parametrize(
    "source_type,scan_type,expected_class",
    (("network", ScanTask.SCAN_TYPE_INSPECT, NetworkInspectTaskRunner),),
)
def test_get_task_runner_class(source_type, scan_type, expected_class):
    """Test get_task_runner_class returns expected class."""
    assert tasks.get_task_runner_class(source_type, scan_type) == expected_class


def test_get_task_runner_class_invalid_type(caplog):
    """Test get_task_runner_class failure with invalid scan type."""
    with pytest.raises(NotImplementedError):
        tasks.get_task_runner_class("network", "potato")
    assert caplog.record_tuples[0][1] == logging.ERROR
    assert "invalid scan_type" in caplog.record_tuples[0][2]


def test_get_task_runner_class_invalid_scanner(caplog):
    """Test get_task_runner_class failure with invalid source type."""
    with pytest.raises(NotImplementedError):
        tasks.get_task_runner_class("potato", ScanTask.SCAN_TYPE_INSPECT)
