#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Queue Manager module."""

import logging
import os
from threading import Thread, Timer
from time import sleep


from api.models import (ScanJob,
                        ScanTask)

from django.db.models import Q

from scanner import ScanJobRunner


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

DEFAULT_HEARTBEAT = 60 * 15
DEFAULT_MAX_TIMEOUT_ORDERLY_SHUTDOWN = 30
RUN_QUEUE_SLEEP_TIME = 5
SCAN_MANAGER_LOG_PREFIX = 'SCAN JOB MANAGER'

try:
    ORDERLY_SHUTDOWN_TIMEOUT_LENGTH = int(
        os.environ.get('MAX_TIMEOUT_ORDERLY_SHUTDOWN',
                       DEFAULT_MAX_TIMEOUT_ORDERLY_SHUTDOWN))
except ValueError:
    ORDERLY_SHUTDOWN_TIMEOUT_LENGTH = DEFAULT_MAX_TIMEOUT_ORDERLY_SHUTDOWN

try:
    HEART_BEAT_INTERVAL = int(os.environ.get('QUIPUCORDS_MANAGER_HEARTBEAT',
                                             DEFAULT_HEARTBEAT))
except ValueError:
    HEART_BEAT_INTERVAL = DEFAULT_HEARTBEAT


class Manager(Thread):
    """Manager of scan job queue."""

    def __init__(self):
        """Initialize the manager."""
        Thread.__init__(self)
        self.scan_queue = []
        self.current_job_runner = None
        self.terminated_job_runner = None
        self.termination_elapsed_time = 0
        self.running = True
        logger.info('%s: Scan manager instance created.',
                    SCAN_MANAGER_LOG_PREFIX)

    def start_log_timer(self):
        """Start log timer."""
        self.log_info()
        heartbeat = Timer(HEART_BEAT_INTERVAL, self.start_log_timer)
        if self.running:
            heartbeat.start()

    def log_info(self):
        """Log the status of the scan manager."""
        current_scan_job = None
        if self.current_job_runner:
            current_scan_job = self.current_job_runner.identifier
            scan_job_message = 'Currently running scan job %s' % \
                current_scan_job
        else:
            scan_job_message = 'No scan job currently running'

        scan_queue_ids = [
            scan_runner.scan_job.id for scan_runner in self.scan_queue]
        scan_queue_ids.reverse()

        logger.info('%s: %s.  Scan queue length is %s. Queued jobs: %s',
                    SCAN_MANAGER_LOG_PREFIX,
                    scan_job_message,
                    len(self.scan_queue),
                    scan_queue_ids)

    def work(self):
        """Start to excute scans in the queue."""
        if len(self.scan_queue) > 0:  # pylint: disable=C1801
            self.current_job_runner = self.scan_queue.pop()
            if self.current_job_runner.scan_job.status in \
                    [ScanTask.PENDING, ScanTask.RUNNING]:
                logger.info('%s: Loading scan job %s.',
                            SCAN_MANAGER_LOG_PREFIX,
                            self.current_job_runner.scan_job.id)
                self.current_job_runner.start()
                self.log_info()
            else:
                error = '%s: Could not start job. Job was not in %s state.' % \
                    (SCAN_MANAGER_LOG_PREFIX, ScanTask.PENDING)
                self.current_job_runner.scan_job.log_message(
                    error, log_level=logging.ERROR)

    def put(self, job):
        """Add job to scan queue.

        :param job: Job to be performed.
        """
        self.scan_queue.insert(0, job)
        self.log_info()

    def kill(self, job, command):
        """Kill a job or remove it from the running queue.

        :param job: The job to kill.
        :returns: True if killed, False otherwise.
        """
        killed = False
        job_id = job.id
        if (self.current_job_runner is not None and
                self.current_job_runner.identifier == job_id and
                self.current_job_runner.is_alive()):

            # record which job is terminated
            self.terminated_job_runner = self.current_job_runner
            self.current_job_runner = None

            job.log_message(
                '%s: Send interrupt to allow job orderly shutdown' %
                SCAN_MANAGER_LOG_PREFIX)
            if command == 'cancel':
                self.terminated_job_runner.manager_interrupt.value = \
                    ScanJob.JOB_TERMINATE_CANCEL
            if command == 'pause':
                self.terminated_job_runner.manager_interrupt.value = \
                    ScanJob.JOB_TERMINATE_PAUSE
            self.termination_elapsed_time = 0
        else:
            logger.info('%s: Checking scan queue for job to remove.',
                        SCAN_MANAGER_LOG_PREFIX)
            removed = False
            for queued_job in self.scan_queue:
                if queued_job.identifier == job_id:
                    self.scan_queue.remove(queued_job)
                    removed = True
                    self.log_info()
                    break
            if removed:
                killed = True
                logger.info('%s: Job %d has been removed from the scan queue.',
                            SCAN_MANAGER_LOG_PREFIX, job_id)
            else:
                logger.info('%s: Job %d was not found in the scan queue.',
                            SCAN_MANAGER_LOG_PREFIX, job_id)
            return killed

    def restart_incomplete_scansjobs(self):
        """Look for incomplete scans and restart."""
        logger.info('%s: Searching for incomplete scans',
                    SCAN_MANAGER_LOG_PREFIX)

        incomplete_scans = ScanJob.objects.filter(
            Q(status=ScanTask.RUNNING) | Q(
                status=ScanTask.PENDING) | Q(status=ScanTask.CREATED)
        ).order_by('-status')
        restarted_scan_count = 0
        for scanjob in incomplete_scans:
            scanner = ScanJobRunner(scanjob)
            logger.info('%s: Adding scan job(id=%d, status=%s, scan_type=%s)',
                        SCAN_MANAGER_LOG_PREFIX, scanjob.id,
                        scanjob.status,
                        scanjob.scan_type)
            if scanjob.status == ScanTask.CREATED:
                scanjob.queue()
            self.put(scanner)
            restarted_scan_count += 1

        if restarted_scan_count == 0:
            logger.info('%s: No running or pending scan jobs to start',
                        SCAN_MANAGER_LOG_PREFIX)

    def run(self):
        """Trigger thread execution."""
        self.restart_incomplete_scansjobs()
        logger.info('%s: Started run loop.', SCAN_MANAGER_LOG_PREFIX)
        self.start_log_timer()
        while self.running:
            queue_len = len(self.scan_queue)
            if self.terminated_job_runner is not None:
                # Occurs when current job was terminated
                killed = not self.terminated_job_runner.is_alive()
                interrupt = self.terminated_job_runner.manager_interrupt
                if killed:
                    # Set this to None so another job can run.
                    self.terminated_job_runner.scan_job.log_message(
                        '%s: Process successfully terminated.' %
                        SCAN_MANAGER_LOG_PREFIX)
                    self.terminated_job_runner = None
                elif interrupt.value == ScanJob.JOB_TERMINATE_ACK:
                    self.terminated_job_runner.log_message(
                        '%s: Scan job acknowledged request to terminate'
                        ' but still processing.' % SCAN_MANAGER_LOG_PREFIX)
                else:
                    self.terminated_job_runner.scan_job.log_message(
                        '%s: Scan job has not acknowledged request'
                        ' to terminate after %ds.' %
                        (SCAN_MANAGER_LOG_PREFIX,
                         self.termination_elapsed_time))

                    # After a time period terminate (will not work in gunicorn)
                    self.termination_elapsed_time += RUN_QUEUE_SLEEP_TIME
                    if self.termination_elapsed_time == \
                            ORDERLY_SHUTDOWN_TIMEOUT_LENGTH:
                        self.terminated_job_runner.scan_job.log_message(
                            'FORCEFUL TERMINATION OF JOB PROCESS')
                        self.terminated_job_runner.terminate()
            elif self.current_job_runner is not None:
                # Occurs when current jobs ends and at least 1 in queue
                killed = not self.current_job_runner.is_alive()
                if killed:
                    self.current_job_runner.scan_job.log_message(
                        '%s: scan job has completed.' %
                        SCAN_MANAGER_LOG_PREFIX)
                    self.current_job_runner = None
                    if queue_len > 0:
                        self.work()
            elif queue_len > 0 and self.current_job_runner is None:
                # Occurs when no current job, but new one added
                self.work()
            sleep(RUN_QUEUE_SLEEP_TIME)


SCAN_MANAGER = Manager()
