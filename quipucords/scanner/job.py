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
from api.models import (ScanTask, Source, ConnectionResults, InspectionResults)
from scanner import network, vcenter


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanJobRunner(Process):
    """ScanProcess perform a group of scan tasks."""

    def __init__(self, scan_job, fact_endpoint):
        """Create discovery scanner."""
        Process.__init__(self)
        self.scan_job = scan_job
        self.fact_endpoint = fact_endpoint
        self.conn_results = None
        self.inspect_results = None

    def initialize_job(self):
        """Initialize the job by creating ScanTasks."""
        if self.scan_job.tasks:
            # It appears the initialization didn't complete
            # so remove partial results
            self.scan_job.tasks.all().delete()
            ConnectionResults.objects.filter(
                scan_job=self.scan_job.id).delete()
            InspectionResults.objects.filter(
                scan_job=self.scan_job.id).delete()

        count = 0
        for source in self.scan_job.sources.all():
            task = ScanTask(source=source,
                            scan_type=ScanTask.SCAN_TYPE_CONNECT,
                            status=ScanTask.PENDING,
                            sequence_number=count)
            count += 1
            task.save()
            self.scan_job.tasks.add(task)

        temp_conn_results = ConnectionResults(scan_job=self.scan_job)
        temp_conn_results.save()

        if self.scan_job.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            temp_inspect_results = InspectionResults(scan_job=self.scan_job)
            temp_inspect_results.save()

        self.scan_job.status = ScanTask.PENDING
        self.scan_job.save()

    def run(self):
        """Trigger thread execution."""
        if self.scan_job.status == ScanTask.CREATED:
            # Job is not ready to run
            self.initialize_job()

        self.conn_results = ConnectionResults.objects.filter(
            scan_job=self.scan_job.id).first()
        self.inspect_results = InspectionResults.objects.filter(
            scan_job=self.scan_job.id).first()

        # Job is not running so start
        self.scan_job.status = ScanTask.RUNNING
        self.scan_job.save()

        # Load tasks that have no been run or are in progress
        task_runners = []
        incomplete_scan_tasks = self.scan_job.tasks.filter(
            Q(status=ScanTask.RUNNING) | Q(status=ScanTask.PENDING)
        ).order_by('sequence_number')
        for scan_task in incomplete_scan_tasks:
            scan_type = scan_task.scan_type
            source_type = scan_task.source.source_type
            if (scan_type == ScanTask.SCAN_TYPE_CONNECT and
                    source_type == Source.NETWORK_SOURCE_TYPE):
                runner = network.ConnectTaskRunner(
                    self.scan_job, scan_task, self.conn_results)
            elif (scan_type == ScanTask.SCAN_TYPE_CONNECT and
                  source_type == Source.VCENTER_SOURCE_TYPE):
                runner = vcenter.ConnectTaskRunner(
                    self.scan_job, scan_task, self.conn_results)
            else:
                logger.error(
                    'Scan task does not have recognized type: %s', scan_task)
                scan_task.status = ScanTask.FAILED
                continue

            task_runners.append(runner)

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
