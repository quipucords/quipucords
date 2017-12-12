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
from api.models import ScanTask
from scanner.task import ScanTaskRunner


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanJobRunner(Process):
    """ScanProcess perform a group of scan tasks."""

    def __init__(self, scanjob, fact_endpoint):
        """Create discovery scanner."""
        Process.__init__(self)
        self.scanjob = scanjob
        self.identifier = scanjob.id
        self.fact_endpoint = fact_endpoint

    def run(self):
        """Trigger thread execution."""
        self.scanjob.status = ScanTask.RUNNING
        self.scanjob.save()

        # Load tasks that have no been run or are in progress
        tasks_to_run = []
        incomplete_scantasks = self.scanjob.tasks.filter(
            Q(status=ScanTask.RUNNING) | Q(status=ScanTask.PENDING)
        ).order_by('sequence_number')
        for scantaskmodel in incomplete_scantasks:
            tasks_to_run.append(ScanTaskRunner(self.scanjob, scantaskmodel))

        print('Running: %s' % self.scanjob)

        for task in tasks_to_run:
            # Mark task as running
            task.scantask.status = ScanTask.RUNNING
            task.scantask.save()

            # run task
            task_status = task.run()

            # Save Task status
            task.scantask.status = task_status
            task.scantask.save()

            if task_status != ScanTask.COMPLETED:
                # Task did not complete successfully so save job status as fail
                self.scanjob.status = ScanTask.FAILED
                self.scanjob.save()

        # All tasks completed successfully
        if self.scanjob.status != ScanTask.FAILED:
            self.scanjob.status = ScanTask.COMPLETED
            self.scanjob.save()

        return self.scanjob.status
