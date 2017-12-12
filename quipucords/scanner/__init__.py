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
"""Scanner used for host connection discovery."""
import logging
from multiprocessing import Process
from api.models import ScanTask
from scanner.task import Task


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Scanner(Process):
    """ScanProcess perform a group of scan tasks."""

    def __init__(self, scanjob, fact_endpoint):
        """Create discovery scanner."""
        Process.__init__(self)
        self.scanjob = scanjob
        self.identifier = scanjob.id
        self.fact_endpoint = fact_endpoint

        # self.source = scanjob.source
        # if conn_results is None:
        #     self.conn_results = ConnectionResults(scan_job=self.scanjob)
        #     self.scan_restart = False
        # else:
        #     self.conn_results = conn_results
        #     self.scan_restart = True

    def run(self):
        """Trigger thread execution."""
        self.scanjob.status = ScanTask.RUNNING
        self.scanjob.save()

        # FIXME load partial results and sort.
        # Doing dumb method now.

        tasks_to_run = []
        for scantaskmodel in self.scanjob.tasks.all():
            tasks_to_run.append(Task(self.scanjob, scantaskmodel))


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
                break

        # All tasks completed successfully
        self.scanjob.status = ScanTask.COMPLETED
        self.scanjob.save()
