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

from api.models import ScanJob, ScanTask


class ScanTaskRunner():
    """ScanTaskRunner is a logical breakdown of work."""

    # pylint: disable=too-few-public-methods
    def __init__(self, scan_job, scan_task, supports_partial_results=False):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param supports_partial_results: Indicates if task supports
            partial results.
        """
        self.scan_job = scan_job
        self.scan_task = scan_task
        self.supports_partial_results = supports_partial_results

        if not supports_partial_results:
            self.scan_task.reset_stats()
            if self.scan_task.scan_type == ScanTask.SCAN_TYPE_CONNECT:
                self.scan_task.connection_result.systems.all().delete()
            elif self.scan_task.scan_type == ScanTask.SCAN_TYPE_INSPECT:
                self.scan_task.inspection_result.systems.all().delete()
            elif self.scan_task.scan_type == ScanTask.SCAN_TYPE_FINGERPRINT:
                details_report = self.scan_task.details_report
                if details_report:
                    # remove results from previous interrupted scan
                    deployment_report = details_report.deployment_report

                    if deployment_report:
                        # remove partial results
                        self.scan_task.log_message(
                            'REMOVING PARTIAL RESULTS - deleting %d '
                            'fingerprints from previous scan'
                            % len(deployment_report.system_fingerprints.all()))
                        deployment_report.system_fingerprints.all().delete()
                        deployment_report.save()
                        details_report.deployment_report = None
                        details_report.save()
                        deployment_report.delete()

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
        # pylint: disable=unused-argument
        # Make sure job is not cancelled or paused
        if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            error_message = 'Scan canceled'
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return error_message, ScanTask.CANCELED

        if manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            error_message = 'Scan paused'
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return error_message, ScanTask.PAUSED

        return 'Task ran successfully', ScanTask.COMPLETED

    def __str__(self):
        """Convert to string."""
        return '{' + 'scan_job:{}, '\
            'sequence_number: {}, '\
            'scan_task: {}'.format(self.scan_job.id,
                                   self.scan_task.sequence_number,
                                   self.scan_task) + '}'
