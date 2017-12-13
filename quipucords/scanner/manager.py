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

"""Queue Manager module."""

import logging
from time import sleep
from threading import Thread
from api.models import ScanTask, ScanJob
from scanner import ScanJobRunner
from django.db.models import Q
from django.core.urlresolvers import reverse
from quipucords.settings import SERVER_URL

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Manager(Thread):
    """Manager of scan job queue."""

    def __init__(self):
        """Initialize the manager."""
        Thread.__init__(self)
        self.scan_queue = []
        self.current_task = None
        self.running = True
        logger.debug('Scan manager created.')

    def work(self):
        """Start to excute scans in the queue."""
        if len(self.scan_queue) > 0:  # pylint: disable=C1801
            self.current_task = self.scan_queue.pop()
            logger.debug('Scan manager running %s.', self.current_task)
            self.current_task.start()
            self.current_task.join()
            self.current_task = None

    def put(self, task):
        """Add task to scan queue.

        :param task: Task to be performed.
        """
        self.scan_queue.insert(0, task)

    def kill(self, task_id):
        """Kill a task or remove it from the running queue.

        :param task_id: The identifier of the task to queue.
        :returns: True if killed, False otherwise.
        """
        killed = False
        logger.info('Killing task %d', task_id)
        logger.debug('Current task is %s.', self.current_task)
        if (self.current_task is not None and
                self.current_task.identifier == task_id and
                self.current_task.is_alive()):
            self.current_task.terminate()
            self.current_task = None
            killed = True
        else:
            logger.debug('Checking scan queue for task to remove.')
            removed = False
            for task in self.scan_queue:
                if task.identifier == task_id:
                    self.scan_queue.remove(task)
                    removed = True
                    break
            if removed:
                killed = True
                logger.debug('Task %d has been removed from the scan queue.',
                             task_id)
            else:
                logger.debug('Task %d was not found in the scan queue.',
                             task_id)
            return killed

    def look_for_incomplete_scans(self):
        """Look for incomplete scans."""
        logger.debug('Scan manager searching for incomplete scans')

        incomplete_scans = ScanJob.objects.filter(
            Q(status=ScanTask.RUNNING) | Q(
                status=ScanTask.PENDING) | Q(status=ScanTask.CREATED)
        ).order_by('-status')
        fact_endpoint = SERVER_URL + reverse('facts-list')
        restarted_scan_count = 0
        for scanjob in incomplete_scans:
            scanner = ScanJobRunner(scanjob, fact_endpoint)
            logger.debug('Adding ScanJob(id=%d, status=%s, scan_type=%s)',
                         scanjob.id, scanjob.status, scanjob.scan_type)
            self.put(scanner)
            restarted_scan_count += 1

        if restarted_scan_count == 0:
            logger.debug('No running or pending scan jobs to start')

    def run(self):
        """Trigger thread execution."""
        self.look_for_incomplete_scans()
        logger.debug('Scan manager started.')
        while self.running:
            queue_len = len(self.scan_queue)
            if queue_len > 0 and self.current_task is None:
                self.work()
            sleep(5)


SCAN_MANAGER = Manager()
