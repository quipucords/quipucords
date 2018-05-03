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

DEFAULT_HEARTBEAT = 60 * 60
MAX_TIMEOUT_ORDERLY_SHUTDOWN = 30


class Manager(Thread):
    """Manager of scan job queue."""

    def __init__(self):
        """Initialize the manager."""
        Thread.__init__(self)
        self.scan_queue = []
        self.current_task = None
        self.running = True
        logger.debug('Scan manager created.')

    def log_info(self):
        """Log the status of the scan manager."""
        try:
            interval = int(os.environ.get('QUIPUCORDS_MANAGER_HEARTBEAT',
                                          DEFAULT_HEARTBEAT))
        except ValueError:
            interval = DEFAULT_HEARTBEAT
        heartbeat = Timer(interval, self.log_info)
        current_scan_job = None
        if self.current_task:
            current_scan_job = self.current_task.identifier
        logger.info('Scan Manager Stats: '
                    'current_scan_job=%s. '
                    'queue_length=%s.',
                    current_scan_job, len(self.scan_queue))
        if self.running:
            heartbeat.start()

    def work(self):
        """Start to excute scans in the queue."""
        if len(self.scan_queue) > 0:  # pylint: disable=C1801
            self.current_task = self.scan_queue.pop()
            if self.current_task.scan_job.status in \
                    [ScanTask.PENDING, ScanTask.RUNNING]:
                logger.debug('Scan manager running %s.', self.current_task)
                self.current_task.start()
                self.current_task.join()
                self.current_task = None
            else:
                error = 'Could not start job. Job was not in %s state.' % \
                    ScanTask.PENDING
                self.current_task.scan_job.log_message(
                    error, log_level=logging.ERROR)

    def put(self, task):
        """Add task to scan queue.

        :param task: Task to be performed.
        """
        self.scan_queue.insert(0, task)

    def kill(self, job, command):
        """Kill a task or remove it from the running queue.

        :param job: The task to kill.
        :returns: True if killed, False otherwise.
        """
        killed = False
        job_id = job.id
        if (self.current_task is not None and
                self.current_task.identifier == job_id and
                self.current_task.is_alive()):
            job_runner = self.current_task
            job.log_message('Send interrupt to allow job orderly shutdown')
            if command == 'cancel':
                job_runner.manager_interrupt.value = \
                    ScanJob.JOB_TERMINATE_CANCEL
            if command == 'pause':
                job_runner.manager_interrupt.value = \
                    ScanJob.JOB_TERMINATE_PAUSE
            count = 0
            interrupt = job_runner.manager_interrupt
            while interrupt.value != ScanJob.JOB_TERMINATE_ACK and \
                    count < MAX_TIMEOUT_ORDERLY_SHUTDOWN:
                job.log_message(
                    'Waiting for job to perform orderly shutdown.  '
                    'Elapsed time: %ds.' % count)
                sleep(1)
                count += 1
            job.log_message('TERMINATING JOB PROCESS')
            job_runner.terminate()
            job_runner.join()
            killed = not job_runner.is_alive()
            job.log_message(
                'Process successfully terminted=%s.' % killed)
            if not killed:
                job.log_message(
                    'Request to terminate process failed.',
                    log_level=logging.ERROR)
            self.current_task = None
        else:
            logger.debug('Checking scan queue for task to remove.')
            removed = False
            for queued_job in self.scan_queue:
                if queued_job.identifier == job_id:
                    self.scan_queue.remove(queued_job)
                    removed = True
                    break
            if removed:
                killed = True
                logger.debug('Task %d has been removed from the scan queue.',
                             job_id)
            else:
                logger.debug('Task %d was not found in the scan queue.',
                             job_id)
            return killed

    def restart_incomplete_scansjobs(self):
        """Look for incomplete scans and restart."""
        logger.debug('Scan manager searching for incomplete scans')

        incomplete_scans = ScanJob.objects.filter(
            Q(status=ScanTask.RUNNING) | Q(
                status=ScanTask.PENDING) | Q(status=ScanTask.CREATED)
        ).order_by('-status')
        restarted_scan_count = 0
        for scanjob in incomplete_scans:
            scanner = ScanJobRunner(scanjob)
            logger.debug('Adding ScanJob(id=%d, status=%s, scan_type=%s)',
                         scanjob.id, scanjob.status, scanjob.scan_type)
            if scanjob.status == ScanTask.CREATED:
                scanjob.queue()
            self.put(scanner)
            restarted_scan_count += 1

        if restarted_scan_count == 0:
            logger.debug('No running or pending scan jobs to start')

    def run(self):
        """Trigger thread execution."""
        self.restart_incomplete_scansjobs()
        logger.debug('Scan manager started.')
        self.log_info()
        while self.running:
            queue_len = len(self.scan_queue)
            if queue_len > 0 and self.current_task is None:
                self.work()
            sleep(5)


SCAN_MANAGER = Manager()
