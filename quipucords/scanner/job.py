#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ScanJobRunner runs a group of scan tasks."""
import logging
from multiprocessing import Process
from django.db.models import Q
from api.models import (ScanTask)
from scanner.task import ScanTaskRunner


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanJobRunner(Process):
    """ScanProcess perform a group of scan tasks."""

    def __init__(self, scan_job, fact_endpoint):
        """Create discovery scanner."""
        Process.__init__(self)
        self.scan_job = scan_job
        self.fact_endpoint = fact_endpoint

    def initialize_job(self):
        """Initialize the job by creating ScanTasks."""
        pass

    def run(self):
        """Trigger thread execution."""
        if self.scan_job.status == ScanTask.CREATED:
            self.initialize_job()

        self.scan_job.status = ScanTask.RUNNING
        self.scan_job.save()

        # Load tasks that have no been run or are in progress
        task_runners = []
        incomplete_scan_tasks = self.scan_job.tasks.filter(
            Q(status=ScanTask.RUNNING) | Q(status=ScanTask.PENDING)
        ).order_by('sequence_number')
        for scan_task in incomplete_scan_tasks:
            task_runners.append(ScanTaskRunner(self.scan_job, scan_task))

        logger.info('ScanJob %s started', self.scan_job.id)

        for runner in task_runners:
            # Mark runner as running
            runner.scan_task.status = ScanTask.RUNNING
            runner.scan_task.save()

            logger.info('Running task: %s', runner)
            # run runner
            task_status = runner.run()

            # Save Task status
            runner.scan_task.status = task_status
            runner.scan_task.save()

            if task_status != ScanTask.COMPLETED:
                # Task did not complete successfully so save job status as fail
                self.scan_job.status = ScanTask.FAILED
                self.scan_job.save()

        # All tasks completed successfully
        if self.scan_job.status != ScanTask.FAILED:
            self.scan_job.status = ScanTask.COMPLETED
            self.scan_job.save()

        logger.info('ScanJob %s ended', self.scan_job.id)
        return self.scan_job.status

    def __str__(self):
        """Convert to string."""
        return '{' + 'scan_job:{}, '\
            'fact_endpoint: {}'.format(self.scan_job.id,
                                       self.fact_endpoint) + '}'
