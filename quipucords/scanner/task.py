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
"""ScanTaskRunner is a logical breakdown of work."""

from api.models import ScanTask


class ScanTaskRunner():
    """ScanTaskRunner is a logical breakdown of work."""

    # pylint: disable=too-few-public-methods
    def __init__(self, scan_job, scan_task):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param prerequisite_tasks: An array of scan task model objects
        that were execute prior to running this task.
        """
        self.scan_job = scan_job
        self.scan_task = scan_task

        if self.scan_task.scan_type == ScanTask.SCAN_TYPE_CONNECT:
            # If we're restarting the scan after a pause, systems that
            # were previously up might be down. So we throw out any
            # partial results and start over.
            self.scan_task.connection_result.systems.all().delete()

    def run(self, manager_interrupt):
        """Block that will be executed.

        Results are expected to be persisted.  The state of
        self.scan_task should be updated with status COMPLETE/FAILED
        before returning.

        :param manager_interrupt: Shared memory Value which can inform
        a task of the need to shutdown immediately
        :returns: Returns a status message to be saved/displayed and
        the ScanTask.STATUS_CHOICES status
        """
        # pylint: disable=no-self-use,unused-argument
        return 'Task ran successfully', ScanTask.COMPLETED

    def __str__(self):
        """Convert to string."""
        return '{' + 'scan_job:{}, '\
            'sequence_number: {}, '\
            'scan_task: {}'.format(self.scan_job.id,
                                   self.scan_task.sequence_number,
                                   self.scan_task) + '}'
