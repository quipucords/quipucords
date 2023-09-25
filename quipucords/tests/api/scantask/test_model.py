"""Test ScanTask model."""

import logging

import pytest

from api.models import Report, ScanTask
from tests.factories import ScanTaskFactory


@pytest.mark.django_db
class TestLoggingRawFacts:
    """Test ScanTask.log_raw_facts method."""

    def test_greenpath(self, caplog):
        """Test logging_raw_facts method "greenpath"."""
        report = Report(sources=[{"mamao": "papaia"}])
        report.save()
        scan_task: ScanTask = ScanTaskFactory(job__report=report)
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
        scan_task: ScanTask = ScanTaskFactory()
        caplog.clear()
        scan_task.log_raw_facts(log_level=log_level)
        assert [rec.levelno for rec in caplog.records] == [log_level] * 3

    def test_logging_raw_facts_no_details_report(self, caplog):
        """Test logging_raw_facts method for a ScanTask w/o details report."""
        scan_task: ScanTask = ScanTaskFactory(job__report=None)
        caplog.set_level(logging.ERROR)
        scan_task.log_raw_facts()
        assert "Missing details report - Impossible to log raw facts." in caplog.text

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
        scan_task: ScanTask = ScanTaskFactory(job__report=None)
        caplog.clear()
        scan_task.log_raw_facts(log_level=set_level)
        assert caplog.record_tuples == [
            ("api.scantask.model", expected_level, mocker.ANY)
        ]
