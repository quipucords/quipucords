"""Test ScanTask model."""

import logging

import pytest

from api.models import ScanTask
from tests.factories import ScanTaskFactory


@pytest.mark.django_db
class TestLoggingRawFacts:
    """Test ScanTask.log_raw_facts method."""

    def test_greenpath(self, caplog):
        """Test logging_raw_facts method "greenpath"."""
        scan_task: ScanTask = ScanTaskFactory(with_raw_facts=[{"mamao": "papaia"}])
        caplog.clear()
        scan_task.log_raw_facts()
        assert [rec.message for rec in caplog.records] == [
            "--------------------raw facts---------------------",
            "[{'mamao': 'papaia'}]",
            "--------------------------------------------------",
        ]

    @pytest.mark.parametrize("log_level", (logging.INFO, logging.ERROR))
    def test_log_level(self, caplog, log_level):
        """Test logging_raw_facts method "greenpath"."""
        scan_task: ScanTask = ScanTaskFactory(
            job__report=None, with_raw_facts=[{"foo": "bar"}]
        )
        caplog.clear()
        scan_task.log_raw_facts(log_level=log_level)
        assert [rec.levelno for rec in caplog.records] == [log_level] * 3

    def test_logging_no_raw_facts(self, caplog):
        """Test logging_raw_facts method for a ScanTask w/o details report."""
        scan_task: ScanTask = ScanTaskFactory(job__report=None)
        caplog.set_level(logging.ERROR)
        scan_task.log_raw_facts()
        assert "Impossible to log absent raw facts." in caplog.text

    @pytest.mark.parametrize(
        "set_level,expected_level",
        [
            (logging.INFO, logging.ERROR),
            (logging.CRITICAL, logging.CRITICAL),
            (logging.ERROR, logging.ERROR),
        ],
    )
    def test_log_level_on_error(self, caplog, set_level, expected_level, mocker):
        """Test if the log level is set correctly on error (mininum lvl is ERROR)."""
        scan_task: ScanTask = ScanTaskFactory()
        caplog.clear()
        scan_task.log_raw_facts(log_level=set_level)
        assert caplog.record_tuples == [
            ("api.scantask.model", expected_level, mocker.ANY)
        ]
