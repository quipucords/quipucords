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

from django.db.models import Q

from api.fact.util import (build_sources_from_tasks,  # noqa I100
                           get_or_create_fact_collection,
                           validate_fact_collection_json)
from api.models import (FactCollection,
                        ScanJob,
                        ScanTask,
                        Source)

from fingerprinter import pfc_signal

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

    # pylint: disable=inconsistent-return-statements
    def run(self):
        """Trigger thread execution."""
        # pylint: disable=too-many-locals,too-many-statements
        # pylint: disable=too-many-return-statements,too-many-branches
        # check to see if manager killed job
        if self.manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            self.manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return ScanTask.CANCELED

        if self.manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            self.manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
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
        for scan_task in incomplete_scan_tasks:
            runner = self._create_task_runner(scan_task)
            if not runner:
                error_message = 'Scan task does not  have recognized '\
                    'type/source combination: %s' % scan_task

                scan_task.fail(error_message)
                self.scan_job.fail(error_message)
                return

            task_runners.append(runner)

        self.scan_job.log_message(
            'Job has %d remaining tasks' % len(incomplete_scan_tasks))

        failed_tasks = []
        for runner in task_runners:
            # Mark runner as running
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
            if task_status == ScanTask.FAILED:
                runner.scan_task.fail(status_message)
            elif task_status == ScanTask.CANCELED:
                runner.scan_task.cancel()
                return ScanTask.CANCELED
            elif task_status == ScanTask.PAUSED:
                runner.scan_task.pause()
                return ScanTask.PAUSED
            elif task_status == ScanTask.COMPLETED:
                runner.scan_task.complete(status_message)
            else:
                error_message = 'ScanTask %d failed.  Scan task must return '\
                    'ScanTask.COMPLETED or ScanTask.FAILED.  '\
                    'ScanTask returned %s' %\
                    (runner.scan_task.id, task_status)
                runner.scan_task.fail(error_message)

            if task_status != ScanTask.COMPLETED:
                # Task did not complete successfully so save job status as fail
                failed_tasks.append(runner.scan_task)

        if bool(failed_tasks):
            failed_task_ids = ', '.join([str(task.id)
                                         for task in failed_tasks])
            error_message = 'The following tasks failed: %s' % failed_task_ids
            self.scan_job.fail(error_message)

        if self.scan_job.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            self._send_facts_to_engine()

        # All tasks completed successfully and sent to endpoint
        if self.scan_job.status != ScanTask.FAILED:
            self.scan_job.complete()

        return self.scan_job.status

    def _create_task_runner(self, scan_task):
        """Create ScanTaskRunner using scan_type and source_type."""
        scan_type = scan_task.scan_type
        source_type = scan_task.source.source_type
        runner = None
        if (scan_type == ScanTask.SCAN_TYPE_CONNECT and
                source_type == Source.NETWORK_SOURCE_TYPE):
            runner = network.ConnectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_CONNECT and
              source_type == Source.VCENTER_SOURCE_TYPE):
            runner = vcenter.ConnectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_CONNECT and
              source_type == Source.SATELLITE_SOURCE_TYPE):
            runner = satellite.ConnectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_INSPECT and
              source_type == Source.NETWORK_SOURCE_TYPE):
            runner = network.InspectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_INSPECT and
              source_type == Source.VCENTER_SOURCE_TYPE):
            runner = vcenter.InspectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_INSPECT and
              source_type == Source.SATELLITE_SOURCE_TYPE):
            runner = satellite.InspectTaskRunner(
                self.scan_job, scan_task)
        return runner

    # pylint: disable=inconsistent-return-statements
    def _send_facts_to_engine(self):
        """Send collected host scan facts to fact endpoint.

        :param facts: The array of fact dictionaries
        :returns: Identifer for the sent facts
        """
        inspect_tasks = self.scan_job.tasks.filter(
            scan_type=ScanTask.SCAN_TYPE_INSPECT).order_by('sequence_number')
        sources = build_sources_from_tasks(inspect_tasks.all())
        if bool(sources):
            fact_collection_json = {'sources': sources}
            has_errors, validation_result = validate_fact_collection_json(
                fact_collection_json)

            if has_errors:
                message = 'Scan producted invalid fact collection JSON: %s' % \
                    validation_result
                self.scan_job.fail(message)
                return

            # Create FC model and save data to JSON file
            fact_collection = get_or_create_fact_collection(
                fact_collection_json, scan_job=self.scan_job)

            # Send signal so fingerprint engine processes raw facts
            try:
                pfc_signal.send(sender=self.__class__,
                                instance=fact_collection)
                # Transition from persisted to complete after processing
                fact_collection.status = FactCollection.FC_STATUS_COMPLETE
                fact_collection.save()
                logger.debug(
                    'Fact collection %d successfully processed.',
                    fact_collection.id)
            except Exception as error:
                # Transition from persisted to failed after engine failed
                fact_collection.status = FactCollection.FC_STATUS_FAILED
                fact_collection.save()
                error_message = 'Fact collection %d failed'\
                    ' to be processed.' % fact_collection.id
                # Mark scanjob failed to avoid re-running on restart
                self.scan_job.fail(error_message)

                logger.error('%s:%s', error.__class__.__name__, error)
                raise error
        else:
            logger.error('No facts gathered from scan.')
            return None

    def __str__(self):
        """Convert to string."""
        return '{' + 'scan_job:{}, '.format(self.scan_job.id) + '}'
