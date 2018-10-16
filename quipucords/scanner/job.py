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
"""ScanJobRunner runs a group of scan tasks."""
import logging
from multiprocessing import Process, Value

from api.fact.util import (build_sources_from_tasks,
                           create_fact_collection,
                           validate_fact_collection_json)
from api.models import (ScanJob,
                        ScanTask,
                        Source)

from django.db.models import Q

from fingerprinter.task import FingerprintTaskRunner

from scanner import network, satellite, vcenter


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanJobRunner(Process):
    """ScanProcess perform a group of scan tasks."""

    def __init__(self, scan_job):
        """Create discovery scanner."""
        Process.__init__(self)
        self.scan_job = scan_job
        self.identifier = scan_job.id
        self.manager_interrupt = Value('i', ScanJob.JOB_RUN)

    def run(self):
        """Trigger thread execution."""
        # pylint: disable=inconsistent-return-statements
        # pylint: disable=no-else-return
        # pylint: disable=too-many-locals,too-many-statements
        # pylint: disable=too-many-return-statements,too-many-branches
        # check to see if manager killed job
        if self.manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            self.manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            self.scan_job.cancel()
            return ScanTask.CANCELED

        if self.manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            self.manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            self.scan_job.pause()
            return ScanTask.PAUSED

        # Job is not running so start
        self.scan_job.start()
        if self.scan_job.status != ScanTask.RUNNING:
            error_message = 'Job could not transition to running state.'\
                '  See error logs.'
            self.scan_job.fail(error_message)
            return ScanTask.FAILED

        # Load tasks that have no been run or are in progress
        task_runners = []

        incomplete_scan_tasks = self.scan_job.tasks.filter(
            Q(status=ScanTask.RUNNING) | Q(status=ScanTask.PENDING)
        ).order_by('sequence_number')
        fingerprint_task_runner = None
        for scan_task in incomplete_scan_tasks:
            runner = self._create_task_runner(scan_task)
            if not runner:
                error_message = 'Scan task does not  have recognized '\
                    'type/source combination: %s' % scan_task

                scan_task.fail(error_message)
                self.scan_job.fail(error_message)
                return ScanTask.FAILED

            if isinstance(runner, FingerprintTaskRunner):
                fingerprint_task_runner = runner
            else:
                task_runners.append(runner)

        self.scan_job.log_message(
            'Job has %d remaining tasks' % len(incomplete_scan_tasks))

        failed_tasks = []
        for runner in task_runners:
            # Mark runner as running

            task_status = self._run_task(runner)

            if task_status == ScanTask.FAILED:
                # Task did not complete successfully
                failed_tasks.append(runner.scan_task)
            elif task_status != ScanTask.COMPLETED:
                # something went wrong or cancel/pause
                return task_status

        if self.scan_job.scan_type in [ScanTask.SCAN_TYPE_INSPECT,
                                       ScanTask.SCAN_TYPE_FINGERPRINT]:
            details_report = fingerprint_task_runner.scan_task.details_report

            if not details_report:
                # Create the details report
                details_report = self._create_fact_collection()

            if not details_report:
                self.scan_job.fail('No facts gathered from scan.')
                return ScanTask.FAILED

            # Associate details report with scan job
            self.scan_job.details_report = details_report
            self.scan_job.save()

            # Associate details report with fingerprint task
            fingerprint_task_runner.scan_task.details_report = details_report
            fingerprint_task_runner.scan_task.save()
            task_status = self._run_task(fingerprint_task_runner)
            if task_status != ScanTask.COMPLETED:
                # Task did not complete successfully
                failed_tasks.append(runner.scan_task)
                fingerprint_task_runner.scan_task.log_message(
                    'Task %s failed.' % (
                        fingerprint_task_runner.scan_task.sequence_number),
                    log_level=logging.ERROR)
            else:
                # Record results for successful tasks
                self.scan_job.report_id = details_report.deployment_report.id
                self.scan_job.save()
                self.scan_job.log_message('Report %d created.' %
                                          self.scan_job.report_id)

        if failed_tasks:
            failed_task_ids = ', '.join([str(task.sequence_number)
                                         for task in failed_tasks])
            error_message = 'The following tasks failed: %s' % failed_task_ids
            self.scan_job.fail(error_message)
            return ScanTask.FAILED

        self.scan_job.complete()
        return ScanTask.COMPLETED

    def _create_task_runner(self, scan_task):
        """Create ScanTaskRunner using scan_type and source_type."""
        # pylint: disable=no-else-return
        scan_type = scan_task.scan_type
        if scan_type == ScanTask.SCAN_TYPE_CONNECT:
            return self._create_connect_task_runner(scan_task)
        elif scan_type == ScanTask.SCAN_TYPE_INSPECT:
            return self._create_inspect_task_runner(scan_task)
        elif scan_type == ScanTask.SCAN_TYPE_FINGERPRINT:
            return FingerprintTaskRunner(self.scan_job, scan_task)
        return None

    def _run_task(self, runner):
        """Run a sigle scan task."""
        # pylint: disable=no-else-return
        if self.manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            self.manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return ScanTask.CANCELED

        if self.manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            self.manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return ScanTask.PAUSED
        runner.scan_task.start()
        # run runner
        try:
            status_message, task_status = runner.run(
                self.manager_interrupt)
        except Exception as error:
            failed_task = runner.scan_task
            context_message = 'Unexpected failure occurred.'
            context_message += 'See context below.\n'
            context_message += 'SCAN JOB: %s\n' % self.scan_job
            context_message += 'TASK: %s\n' % failed_task
            if failed_task.scan_type != ScanTask.SCAN_TYPE_FINGERPRINT:
                context_message += 'SOURCE: %s\n' % failed_task.source
                creds = [str(cred)
                         for cred in failed_task.source.credentials.all()]
                context_message += 'CREDENTIALS: [%s]' % creds
            failed_task.log_message(
                context_message, log_level=logging.ERROR)

            message = 'FATAL ERROR. %s' % str(error)
            self.scan_job.fail(message)
            raise error

        # Save Task status
        if task_status == ScanTask.CANCELED:
            runner.scan_task.cancel()
            runner.scan_job.cancel()
        elif task_status == ScanTask.PAUSED:
            runner.scan_task.pause()
            runner.scan_job.pause()
        elif task_status == ScanTask.COMPLETED:
            runner.scan_task.complete(status_message)
        elif task_status == ScanTask.FAILED:
            runner.scan_task.fail(status_message)
        else:
            error_message = 'ScanTask %d failed.  Scan task must return '\
                'ScanTask.COMPLETED or ScanTask.FAILED. ScanTask returned ' \
                '"%s" and the following status message: %s' %\
                (runner.scan_task.sequence_number, task_status, status_message)
            runner.scan_task.fail(error_message)
            task_status = ScanTask.FAILED
        return task_status

    def _create_connect_task_runner(self, scan_task):
        """Create connection TaskRunner using source_type."""
        source_type = scan_task.source.source_type
        runner = None
        if source_type == Source.NETWORK_SOURCE_TYPE:
            runner = network.ConnectTaskRunner(
                self.scan_job, scan_task)
        elif source_type == Source.VCENTER_SOURCE_TYPE:
            runner = vcenter.ConnectTaskRunner(
                self.scan_job, scan_task)
        elif source_type == Source.SATELLITE_SOURCE_TYPE:
            runner = satellite.ConnectTaskRunner(
                self.scan_job, scan_task)
        return runner

    def _create_inspect_task_runner(self, scan_task):
        """Create inspection TaskRunner using source_type."""
        source_type = scan_task.source.source_type
        runner = None
        if source_type == Source.NETWORK_SOURCE_TYPE:
            runner = network.InspectTaskRunner(
                self.scan_job, scan_task)
        elif source_type == Source.VCENTER_SOURCE_TYPE:
            runner = vcenter.InspectTaskRunner(
                self.scan_job, scan_task)
        elif source_type == Source.SATELLITE_SOURCE_TYPE:
            runner = satellite.InspectTaskRunner(
                self.scan_job, scan_task)
        return runner

    def _create_fact_collection(self):
        """Send collected host scan facts to fact endpoint.

        :param facts: The array of fact dictionaries
        :returns: Identifer for the sent facts
        """
        inspect_tasks = self.scan_job.tasks.filter(
            scan_type=ScanTask.SCAN_TYPE_INSPECT).order_by('sequence_number')
        sources = build_sources_from_tasks(
            inspect_tasks.filter(status=ScanTask.COMPLETED))
        if bool(sources):
            fact_collection_json = {'sources': sources}
            has_errors, validation_result = validate_fact_collection_json(
                fact_collection_json)

            if has_errors:
                message = 'Scan producted invalid details report JSON: %s' % \
                    validation_result
                self.scan_job.fail(message)
                return ScanTask.FAILED

            # Create FC model and save data to JSON file
            details_report = create_fact_collection(
                fact_collection_json)
            return details_report

        return None

    def __str__(self):
        """Convert to string."""
        return '{' + 'scan_job:{}, '.format(self.scan_job.id) + '}'
