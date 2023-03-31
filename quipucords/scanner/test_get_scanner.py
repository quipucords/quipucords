"""Sanity test for quipucords scanners."""

import pytest

from constants import DataSources
from scanner.get_scanner import get_scanner
from scanner.runner import ScanTaskRunner


@pytest.mark.parametrize("data_source", DataSources.values)
def test_scanner_module(data_source):
    """Sanity check scanner packages."""
    scanner = get_scanner(data_source)
    assert issubclass(scanner.ConnectTaskRunner, ScanTaskRunner)
    assert issubclass(scanner.InspectTaskRunner, ScanTaskRunner)


def test_scanner_invalid_source_type():
    """Ensure get_scanner throws an error when a non-implemented scanner is provided."""
    with pytest.raises(NotImplementedError):
        get_scanner("UNKNOWN")
