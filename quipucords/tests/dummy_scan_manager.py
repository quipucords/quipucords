"""Dummy scan manager module - a replacement on [Scan]Manager for tests."""

import logging

from scanner.job import ScanJobRunner

logger = logging.getLogger(__name__)


class DummyScanManager:
    """ScanManager for testing purposes."""

    def __init__(self):
        """Inititialize DummyScanManager."""
        self._queue = []

    def put(self, job):
        """Add job to queue."""
        self._queue.append(job)

    def is_alive(self):
        """Check if DummyScanManager is 'alive'."""
        return True

    def work(self):
        """Execute scan queue synchronously."""
        while self._queue:
            logger.info("=" * 50)
            logger.info("CURRENT QUEUE %s", self._queue)
            job_runner: ScanJobRunner = self._queue.pop()
            logger.info("STARTING JOB %s", job_runner.scan_job)
            job_runner.run()

    def kill(self, job, command):
        """Mimic ScanManager kill method signature."""
